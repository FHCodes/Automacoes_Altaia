#!/usr/bin/env python

__doc__ = \
    '''
'''

__version__ = '0.1'

__authors__ = [
    "Version 0.1: Joao Pio <joao-t-pio@telecom.pt>"
]

# Local Libraries
from tools.logger import namf_logger as namf
import schemas.unit
import schemas.item

# Standard Libraries
import re
import json
from string import Template
from schema import Schema, And, Or, Use, Optional, Regex
from collections import OrderedDict, MutableMapping

# Third Party Libraries
import xmltodict


class DateTemplate(Template):
    delimiter = '%'


class NamfRequest:

    # Class Constructor
    def __init__(self, catalog=None):

        self.schema = None
        self.force_list = None
        self.attribute_prefix = None

        # Catalog in dict format (can be given at instantiation)
        self.catalog = catalog

        # NAMF API request in dict(json) format
        self.api_req = None

        # Python date formats mappings to java
        self.date_mapping = {'Y': 'yyyy', 'm': 'MM', 'd': 'dd', 'H': 'HH', 'M': 'mm', 'S': 'ss'}

    def load_catalog(self, catalog):

        # Convert the input to a dictionary
        self.catalog = xmltodict.parse(catalog, xml_attribs=True, attr_prefix=self.attribute_prefix,
                                       force_list=self.force_list)
        
        for unit in self.catalog["root"]["measUnits"]:
            if unit["measItems"] != [None]:
                for item in unit["measItems"]:
                    if item["measItemType"] == "CM":
                        item["measItemType"] = "MT"
        
    def validate_api_req(self):

        # Check if there is a catalog loaded
        if self.api_req is not None and self.schema is not None:
            return self.schema.validate(self.api_req)
        else:
            raise ValueError("Must load catalog and define schema before validation can take place")


class LoadingRequest(NamfRequest):

    # Class Constructor
    def __init__(self, catalog=None):

        NamfRequest.__init__(self, catalog)
        # Schema defining the format of this json request
        self.schema = Schema(
            {
                "version": Use(str),
                Optional("id"): Use(str),
                "measUnits": [
                    {
                        "active": bool,
                        "description": Use(str),
                        "id": Use(str),
                        "name": Use(str),
                        "partitionOf": Use(str),
                        "stateOrigin": Use(str),
                        "objectType": Use(str),
                        "tableName": Use(str),
                        "tech": Use(str),
                        "udn": Use(str),
                        "measuredObjects": Regex(".*"),
                        "granularityField": Use(str),
                        "granularityUnit": Use(str),
                        "vendorId": Use(str),
                        "useCorrelationFields": Use(str),
                        "measItems": [
                            {
                                "active": bool,
                                "columnName": Use(str),
                                Optional("description"): Use(str),
                                "id": Use(str),
                                "measItemType": Use(str),
                                Optional("name"): Use(str),
                                "stateOrigin": Use(str),
                                "type": Use(str),
                                Optional("typeCust"): Use(str),
                                Optional("typeVendor"): Use(str),
                                "udn": Use(str),
                                Optional("unitVendor"): Use(str),
                                "vendorId": Use(str),
                                Optional("extraItem"): {
                                    "oid": Use(str),
                                    # STRING, HEX, INTEGER, INTEGER32, DISPLAYSTRING, COUNTER, COUNTER32, COUNTER64, GAUGE32, OCTETSTRING, OBJECTIDENTIFIER, IPADDRESS, TIMETICKS, NSAPADDRESS
                                    "type": Or("STRING", "HEX", "INTEGER32", "INTEGER", "DISPLAYSTRING", "COUNTER32", "COUNTER64", "COUNTER", "GAUGE32", "OCTETSTRING", "OBJECTIDENTIFIER", "IPADDRESS", "TIMETICKS", "NSAPADDRESS")
                                }
                            }
                        ]
                    }
                ]
            })

        # Settings for the dictionary
        self.force_list = ["measUnits", "measItems"]
        self.attribute_prefix = ""

    # Static method to be called recursively that reformats the merged catalog nodes into NAMF compliant JSON dicts
    @staticmethod
    def format_dict(api_dict):

        # Start iterating the dictionary
        for base_key, base_value in api_dict.iteritems():

            # Behaviour if it is an OrderedDict
            if isinstance(base_value, OrderedDict):

                # Iterate OrderedDict items
                for key, value in base_value.items():
                    # Happens to be an id and is not the top id of the json
                    if key == "id" and "measUnits" not in base_value.keys():
                        base_value[key] = base_value[key].upper()

                    try:
                        # Value is a boolean (text) and needs to be converted to a boolean type
                        if value.upper() == "TRUE":
                            base_value[key] = True
                            namf.log.debug("Replaced True in {0}".format(key))
                        elif value.upper() == "FALSE":
                            base_value[key] = False
                            namf.log.debug("Replaced True in {0}".format(key))
                    except AttributeError:
                        # Could happen when value is not a string, so ignore it
                        continue

                # Recusively call this function, since base_value is a dict
                LoadingRequest.format_dict(base_value)

            # Behaviour if it is a list
            elif isinstance(base_value, list):
                # Iterate list members
                for list_member in base_value:
                    if list_member is None:
                        base_value.pop()

                    # Behaviour if it is an OrderedDict
                    if isinstance(list_member, OrderedDict):

                        # Adds the "active" attribute that wasn't present in items of the merged catalog
                        if "columnName" in list_member.keys():
                            list_member["active"] = True

                        # Iterate OrderedDict items
                        for key, value in list_member.items():
                            # Capitalizes id
                            if key == "id":
                                list_member[key] = list_member[key].upper()

                            try:
                                # Value is a boolean (text) and needs to be converted to a boolean type
                                if value.upper() == "TRUE":
                                    list_member[key] = True
                                    namf.log.debug("Replaced True in {0}".format(key))
                                elif value.upper() == "FALSE":
                                    list_member[key] = False
                                    namf.log.debug("Replaced True in {0}".format(key))
                            except AttributeError:
                                continue

                        # Recusively call this function, since list_member is a dict
                        LoadingRequest.format_dict(list_member)

            elif base_key in ["oid", "oidtype"]:

                value = api_dict.pop(base_key)

                # Correct "oidtype" because "type" already existed
                if base_key == "oidtype":
                    base_key = "type"

                if "extraItem" in api_dict:
                    api_dict["extraItem"][base_key] = value
                else:
                    api_dict["extraItem"] = {base_key: value}

    def build_api_req(self):

        # Remove the root tag
        dict_req = self.catalog["root"]

        # Format the dictionary to be NAMF API compliant
        self.format_dict(dict_req)

        self.api_req = dict_req

    def add_origin_units(self):

        # Add origin units (unitSplit)
        origin_units = dict()
        for unit in self.api_req["measUnits"]:
            if unit["id"] != unit["partitionOf"]:
                origin_units[unit["partitionOf"]] = {"id": unit["partitionOf"], "cloneUnit": unit["id"]}

        # add the extra units
        for extra_unit in origin_units.keys():
            self.api_req["measUnits"].append(origin_units[extra_unit])

    def deactivate_from_list(self, families, identifier_type):

        # if identifier_type is all, then deactivate all families
        if identifier_type in ["all"]:
            for fam in self.api_req["measUnits"]:
                fam["active"] = False
            return

        # if identifier_type is none, do nothing
        if identifier_type in ["none"]:
            return

        # validate identifier type - acceptable values are tableName or id
        if identifier_type not in ["tableName", "id"]:
            namf.log.error(
                "Can't deactivate families due to: Must provide field of table identification. Accepted values are ['tableName', 'id']")
            return
        # validate list
        elif len(families) < 1 or not isinstance(families, list):
            namf.log.error("Can't deactivate families due to: Families list must be a non-empty list")
            return
        else:
            # deactivate families contained in the list
            for fam in self.api_req["measUnits"]:
                if fam[identifier_type] in families:
                    fam["active"] = False

    def activate_from_list(self, families, identifier_type):

        # if identifier_type is all, then activate all families
        if identifier_type in ["all"]:
            for fam in self.api_req["measUnits"]:
                fam["active"] = True
            return

        # if identifier_type is none, do nothing
        if identifier_type in ["none"]:
            return

        # validate identifier type - acceptable values are tableName or id
        if identifier_type not in ["tableName", "id"]:
            namf.log.error(
                "Can't activate families due to: Must provide field of table identification. Accepted values are ['tableName', 'id']")
            return
        # validate list
        elif len(families) < 1 or not isinstance(families, list):
            namf.log.error("Can't activate families due to: Families list must be a non-empty list")
            return
        else:
            # activate families contained in the list
            for fam in self.api_req["measUnits"]:
                if fam[identifier_type] in families:
                    fam["active"] = True


class TransformRequest(NamfRequest):

    # Class Constructor
    def __init__(self, catalog=None, families_list=None, configurations=None):

        NamfRequest.__init__(self, catalog)

        # Schema defining the format of this json request main body
        self.schema = Schema(
            {
                "version": Use(str),
                Optional("id"): Use(str),
                "measUnits": [
                    {
                        "id": Use(str),
                        Optional("operations"): [
                            {
                                "type": Use(str),
                                "def": Use(list)
                            }
                        ],
                        Optional("measItems"): [
                            {
                                "id": Use(str),
                                "operations": [
                                    {
                                        "type": Use(str),
                                        Optional("optional"): Use(bool),
                                        "def": Use(list)
                                    }
                                ]
                            }
                        ],
                        Optional("cloneUnit"): Use(str)
                    }
                ]
            })

        # Settings for the dictionary
        self.force_list = ['unit', 'item', 'operation', 'newField', 'item', 'fields', 'allow', 'regex', 'sharedField', 'measurement']
        self.attribute_prefix = ""

        # Configurations
        self.confs = configurations

        # Catalog in dict format (can be given at instantiation)
        self.catalog = catalog

        # Families list - used to generate empty transform families (required by NAMF)
        self.families_list = families_list

        # Units to add after refactoring operations (from unitSplit)
        self.target_families = []

        # Operations schema dictionary
        self.ops_schemas = {"unit": {}, "item": {}}
        # Operations dictionary
        self.ops_dict = {"unit": {}, "item": {}}

        namf.log.debug("Loading transform operations schemas:")

        # Load all the different unit and item operation schemas from the schema module
        for unit_op in schemas.unit.__all__:

            op_mod = __import__("schemas.unit.%s" % unit_op, fromlist=schemas.unit.__all__)
            self.ops_schemas["unit"][unit_op] = op_mod.schema_def
            namf.log.debug("Unit {0} schema loaded.".format(unit_op))

            # Also create a list with the field names for changes related with pluralization of names
            self.ops_dict["unit"][unit_op] = []
            try:
                for field in op_mod.schema_def._schema[0].keys():
                    try:
                        self.ops_dict["unit"][unit_op].append(field._schema)
                    except AttributeError:
                        self.ops_dict["unit"][unit_op].append(field)
                        continue
            except IndexError:
                # Must be an empty schema (several operations have empty defs)
                pass

        for item_op in schemas.item.__all__:

            op_mod = __import__("schemas.item.%s" % item_op, fromlist=schemas.item.__all__)
            self.ops_schemas["item"][item_op] = op_mod.schema_def
            namf.log.debug("Item {0} schema loaded.".format(item_op))

            # Also create a list with the field names for changes related with pluralization of names
            self.ops_dict["item"][item_op] = []
            try:
                for field in op_mod.schema_def._schema[0].keys():

                    try:
                        self.ops_dict["item"][item_op].append(field._schema)
                    except AttributeError:
                        self.ops_dict["item"][item_op].append(field)
                        continue
            except IndexError:
                # Must be an empty schema (several operations have empty defs)
                pass

    # Method override for load_catalog to provision for transform catalog specific requirements (not a dictionary, but a file)
    def load_catalog(self, catalog_path):

        # Convert the input to a dictionary
        with open(catalog_path) as catfile:
            self.catalog = xmltodict.parse(catfile.read(), xml_attribs=True, attr_prefix=self.attribute_prefix,
                                           force_list=self.force_list)

    # Static method to be called recursively that flattens operation nodes to comply with NAMF
    @staticmethod
    def flatten(dictionary):

        items = []

        boolean_dict = {"TRUE": True, "FALSE": False}

        for key, value in dictionary.items():

            # Replace strings with "True" or "False" with their boolean equivalents
            try:
                value = boolean_dict[value.upper()]
            except KeyError:
                pass
            except AttributeError:
                pass

            new_key = key

            # Checks if the value is an instance of dict, collections.defaultdict, collections.OrderedDict or collections.Counter
            if isinstance(value, MutableMapping):
                # Extends the items list with the resulting flattened list
                items.extend(TransformRequest.flatten(value).items())
                # print "extend {0}".format(items)
            else:
                # Simply appends the key and value to the items list
                items.append((new_key, value))
                # print "append {0}".format(items)

        # Returns a dictionary made with the tuple list

        return dict(items)

    # Method to refactor operations node of the operations catalog to comply with NAMF
    def refactoroperationsnode(self, operations_dict):

        try:
            operations_dict["operations"] = operations_dict.pop("operation")

            # If operations is not a list, do so
            if not isinstance(operations_dict["operations"], list):
                operations_dict["operations"] = [operations_dict["operations"]]

        except KeyError:
            # The node doesn't have operations. Not critical if it is a unit, so just return
            return

        # List of indexes to remove after verifying if operation is supported
        removal_indexes = []

        for idx, operation in enumerate(operations_dict["operations"]):

            namf.log.debug("Processing operation: {0}".format(operation["type"]))

            # Schema for this operation is defined in the schemas module
            if operation["type"] in self.ops_schemas["unit"].keys() or operation["type"] in self.ops_schemas[
                "item"].keys():

                # remove complexoperation tag
                try:
                    operation.pop("complexoperation")
                except KeyError:
                    pass

                # Gather all sub nodes and put them inside "def"
                clone_op = dict()

                # Flatten the operations xml structure to a one level json inside "def"
                for key in operation.keys():
                    if key != "type" and key != "optional":
                        clone_op[key] = operation[key]
                        operation.pop(key)

                operation["def"] = [self.flatten(clone_op)]

                # print "--------------flatten---------------"
                # print json.dumps(operation, indent=4)
                # print "------------------------------------"
                
                # Add optional support and conversion to bool
                if "optional" in operation:
                    try:
                        if str(operation["optional"]).upper() == "TRUE":
                            operation["optional"] = True
                        else:
                            del operation["optional"]
                    except TypeError:
                        del operation["optional"]

                # print "-------------optional--------------"
                # print json.dumps(operation, indent=4)
                # print "-----------------------------------"

                # -------------------EXCEPTIONS-----------------------------
                if operation["type"] == "concatFields":
                    # Fix stringFromFields and finalString capitalization scheme
                    for df in operation["def"]:
                        df["stringFromFields"] = df.pop("stringfromfields")
                        # finalString is optional
                        try:
                            df["finalString"] = df.pop("finalstring")
                        except KeyError:
                            pass
                # solve regex problem in applyRegex
                if operation["type"] == "applyRegex":

                    # print "--------------applyRegex------------"
                    # print json.dumps(operation, indent=4)
                    # print "------------------------------------"

                    try:
                        list_reg = operation["def"].pop()["regex"]

                        # loop all regex nodes and capitalize patterns
                        for reg in list_reg:
                            # Pattern
                            reg["pattern"] = re.sub("\?P<([^>]+)>", (lambda m: "?P<{0}>".format(m.group(1).upper())),
                                                    reg["pattern"])

                            operation["def"].append(reg)
                            # op_def.append(list_reg.pop(idx))

                    except KeyError:
                        # No regex node
                        pass

                    except Exception:
                        raise Exception("Error fixing applyRegex operation")

                # Insert mongo info for enrichment operation
                if operation["type"] == "enrichment":
                    try:
                        # Apply the default mongo information to the operation (from the configurations file)
                        for df in operation["def"]:
                            df["enrichmentId"] = self.confs.mongo["enrichmentId"]
                            df["datasourceId"] = self.confs.mongo["datasourceId"]

                    except Exception:
                        raise Exception("Error fixing enrichment operation")

                # Solve "#text" problems in fixedValue
                if operation["type"] == "fixedValue":
                    try:
                        df = operation["def"][0]["newField"]
                        for fixed_op in df:
                            for key in fixed_op.keys():
                                if key == "#text":
                                    fixed_op["field"] = fixed_op.pop("#text").upper()
                    except Exception:
                        raise Exception("Error fixing fixedValue operation")

                if operation["type"] == "fixedValueWithPattern":
                    # print "--------------fixedValueWithPattern------------"
                    # print json.dumps(operation, indent=4)
                    # print "------------------------------------"

                    try:
                        list_reg = operation["def"].pop()["regex"]

                        # loop all regex nodes and capitalize patterns
                        for reg in list_reg:
                            # Pattern
                            reg["pattern"] = re.sub("\?P<([^>]+)>", (lambda m: "?P<{0}>".format(m.group(1).upper())),
                                                    reg["pattern"])

                            operation["def"].append({"pattern": reg["pattern"], "newFields": list()})

                            for newfield in reg["newField"]:
                                operation["def"][0]["newFields"].append({"value": newfield["value"], "field": newfield["#text"]})

                    except KeyError:
                        # No regex node
                        pass

                    except Exception:
                        raise Exception("Error fixing fixedValueWithPattern operation")

                # Solve key problems in simpleFilter
                if operation["type"] == "simpleFilter":

                    try:
                        # replace "allow" with "field"
                        for df in operation["def"]:
                            df["field"] = df.pop("allow")
                    except Exception:
                        raise Exception("Error fixing simpleFilter operation")

                # Solve key problems in unitSplitv2 and unitSplit
                if operation["type"] in ["unitSplitv2", "unitSplit"]:
                    try:
                        # replace "regex" with "regexes"
                        for df in operation["def"]:
                            # capitalize the id (it doesn't get done automatically, because originally it was a field and not an id)
                            df["id"] = df["id"].upper()

                            # Change the name of the regex node
                            df["regexes"] = df.pop("regex")

                            for newunit in df["regexes"]:
                                newunit["newUnit"] = newunit.pop("newunit")
                                newunit["newUnit"] = newunit["newUnit"].upper()

                                # Add the target family bracket (necessary to propagate the original family ID)
                                self.target_families.append(
                                    {"id": newunit["newUnit"], "cloneUnit": operations_dict["id"]})
                                namf.log.debug("appended target_families with {0}".format(
                                    {"id": newunit["newUnit"], "cloneUnit": operations_dict["id"]}))

                                # Extract pattern for treatment (old mediation matched only a section of the field,
                                # new mediation matches the entirety of the field
                                pattern = newunit.pop("pattern")

                                # Deal with starting edge
                                pat_match = re.match("^(\^|\.\*|\.\+)", pattern)

                                # Starting edge needs fixing
                                if pat_match is None:
                                    pattern = ".*{0}".format(pattern)

                                # Deal with ending edge
                                pat_search = re.search("(\.\*|\.\+|\.\*\?|\.\+\?|\.\*\$|\.\+\$|\.\*\?\$|\.\+\?\$)$", pattern)

                                # Ending edge needs fixing
                                if pat_search is None:
                                    pattern = "{0}.*".format(pattern)

                                newunit["pattern"] = pattern

                        # change the name of the operation
                        operation["type"] = "unitSplit"

                    except Exception:
                        raise Exception("Error fixing unitSplitv2 operation")

                # Solve dateOperations, filterDocs, convertTimezone field not being capitalized
                if operation["type"] in ["dateOperations", "filterDocs", "convertTimezone"]:
                    try:
                        for df in operation["def"]:
                            df["field"] = df["field"].upper()

                            if operation["type"] == "convertTimezone":
                                try:
                                    df["inTimezone"] = df.pop("in_tz")
                                    df["outTimezone"] = df.pop("out_tz")
                                    df["inPattern"] = df.pop("in_pattern")
                                    df["outPattern"] = df.pop("out_pattern")
                                except KeyError:
                                    pass

                                try:
                                    df["outPattern"] = DateTemplate(df["outPattern"]).substitute(
                                        **self.date_mapping)
                                    df["inPattern"] = DateTemplate(df["inPattern"]).substitute(**self.date_mapping)
                                except Exception as e:
                                    namf.log.warning(
                                            "Problem converting patterns in convertTimezone operation due to {0}.".format(e))
                                    continue

                            # operation["def"][0]["field"] = operation["def"][0]["field"].upper()
                    except Exception:
                        raise Exception("Error fixing {0} operation.".format(operation["type"]))

                # Solve key problems in timestampToEpoch and hexToDec
                if operation["type"] in ["timestampToEpoch", "hexToDec"]:
                    try:
                        operation["def"] = []
                    except Exception:
                        raise Exception("Error fixing {0} operation".format(operation["type"]))

                # Solve key problems in epochtotimestamp as well as applying the input unit
                if operation["type"] in ["epochToTimestamp"]:
                    try:
                        for df in operation["def"]:
                            if "inputTimeUnit" in df.keys():
                                operation["def"] = [{"inputTimeUnit": df["inputTimeUnit"]}]
                            else:
                                operation["def"] = []
                    except Exception as e:
                        raise Exception("Error fixing {0} operation, due to {1}".format(operation["type"], e))

                # Solve empty key node problem in dictionaryReplace
                if operation["type"] in ["dictionaryReplace"]:

                    for items in operation["def"]:
                        for item in items["item"]:
                            if item["key"] is None:
                                item["key"] = ""

                    try:
                        df = operation["def"][0]
                        if "#text" in df.keys():
                            for key in df.keys():
                                if key == "#text":
                                    df.pop("#text")
                    except Exception:
                        raise Exception("Error fixing dictionaryReplace operation")

                    # print "--------dictionaryReplace-----------"
                    # print json.dumps(operation, indent=4)
                    # print "------------------------------------"

                # Solve conditionalMapping
                if operation["type"] in ["conditionalMapping"]:

                    if "if" in operation["def"][0].keys():
                        operation["def"] = operation["def"].pop()["if"]

                    # print "--------conditionalMapping-----------"
                    # print json.dumps(operation, indent=4)
                    # print "------------------------------------"

                # Solve splitMultiValue
                if operation["type"] in ["splitMultiValue"]:

                    # print "--------splitMultiValue-----------"
                    # print json.dumps(operation, indent=4)
                    # print "------------------------------------"

                    try:
                        for d in operation["def"]:
                            if d["compressed"] is False:
                                d["allowMismatchFields"] = True

                    except Exception:
                        raise Exception("Error fixing splitMultiValue operation")
                    
                # Solve int fields previously converted as str in truncateValue
                if operation["type"] in ["truncateValue"]:

                    # print "--------truncateValue-----------"
                    # print json.dumps(operation, indent=4)
                    # print "--------------------------------"
                    
                    try:
                        for d in operation["def"]:
                            d["startIndex"] = int(d["startIndex"])
                            d["endIndex"] = int(d["endIndex"])
                            
                    except Exception:
                        raise Exception("Error converting startIndex or endIndex to int in truncateValue operation")
                        
                # -------------------END OF EXCEPTIONS--------------------------

                # Pluralize names of certain nodes
                for idx2, def_dict in enumerate(operation["def"]):

                    for node_key in def_dict.keys():
                        # if a plural version is found in the schema, alter it
                        plural = "{0}s".format(node_key)

                        try:
                            if plural in self.ops_dict["unit"][operation["type"]]:

                                # It's a list already
                                if isinstance(def_dict[node_key], list):
                                    def_dict[plural] = def_dict.pop(node_key)
                                    # Capitalize fields
                                    for idx3, field in enumerate(def_dict[plural]):
                                        if isinstance(def_dict[plural][idx3], unicode) or isinstance(
                                                def_dict[plural][idx3], str):
                                            def_dict[plural][idx3] = field.upper()

                                # turn into a list
                                else:
                                    def_dict[plural] = [def_dict.pop(node_key).upper()]
                        except IndexError:
                            # Must be an empty schema (several operations have empty defs)
                            continue
                        except KeyError:
                            # It's probably an item operation
                            try:
                                if plural in self.ops_dict["item"][operation["type"]]:

                                    # It's a list already
                                    if isinstance(def_dict[node_key], list):
                                        def_dict[plural] = def_dict.pop(node_key)
                                        # Capitalize field
                                        for idx3, field in enumerate(def_dict[plural]):
                                            if isinstance(def_dict[plural][idx3], unicode) or isinstance(
                                                    def_dict[plural][idx3], str):
                                                def_dict[plural][idx3] = field.upper()
                                    # turn into a list
                                    else:
                                        def_dict[plural] = [def_dict.pop(node_key).upper()]
                            except IndexError:
                                # Must be an empty schema (several operations have empty defs)
                                continue
                            except KeyError as e:
                                raise Exception(
                                    "Operation {0} doesn't seem to have any schema definition due to {1}".format(
                                        operation["type"], e))

            # There is no schema defined for this operation. Exclude it from the API request
            else:
                # Operation not supported by schemas
                namf.log.warning("Excluding operation {0} from transform catalog due to no schema being defined.".format(
                    operation["type"]))
                removal_indexes.append(idx)
                # operations_dict["operations"].pop(idx)
                continue

        copy_operations_dict = operations_dict["operations"]
        operations_dict["operations"] = [op for index, op in enumerate(copy_operations_dict) if
                                         index not in removal_indexes]

    def build_api_req(self, id):

        namf.log.info("Building transform API from operations catalog.")

        # Remove the root tag and any other nodes than unit
        list_req = self.catalog["root"]["unit"]
        # Get the version, vendor and model from the the external configurations
        version = self.confs.gconfs["catalogVersion"]

        # print json.dumps(list_req, indent=4)

        # Loop all the units
        for unit in list_req:
            namf.log.debug("Processing unit: {0}".format(unit["id"]))
            # capitalize the unit IDs
            unit["id"] = unit["id"].upper()
            # Remove potential attributes existing in operations catalog but not allowed in NAMF
            for attribute in unit.keys():
                if attribute.upper() in ["TYPEID"]:
                    unit.pop(attribute)

            # Remove unit from the families_list used for adding families without operations
            if unit["id"] in self.families_list:
                namf.log.debug("Removing unit {0} from list of no operations units".format(unit["id"]))
                self.families_list.remove(unit["id"])

            if "item" in unit.keys():
                # Rename item to measItems
                unit["measItems"] = unit.pop("item")

                # Loop all the items
                for item in unit["measItems"]:
                    namf.log.debug("Processing item: {0}".format(item["id"]))
                    # capitalize the item IDs
                    item["id"] = item["id"].upper()
                    # Alter the operations to the format required by NAMF
                    self.refactoroperationsnode(item)
                    # print "----------ITEM------------"
                    # print json.dumps(item, indent=4)
                    # print "--------------------------"

            self.refactoroperationsnode(unit)

            # print "----------UNIT------------"
            # print json.dumps(unit, indent=4)
            # print "--------------------------"

        # add the extra units necessary due to unitSplit
        for extra_unit in self.target_families:
            extra_unit_present = False

            for meas_unit in list_req:
                if extra_unit["id"] == meas_unit["id"]:
                    extra_unit_present = True
                    meas_unit["cloneUnit"] = extra_unit["cloneUnit"]

            if not extra_unit_present:
                list_req.append(extra_unit)

        # Add families not present in operations catalog, but existing in client catalog (NAMF requirement)
        for cfamily in self.families_list:
            list_req.append({"id": cfamily, "operations": []})

        if id is None:
            self.api_req = {"version": version, "id": "{{ catalogID }}", "measUnits": list_req}
        else:
            self.api_req = {"version": version, "id": id, "measUnits": list_req}

        # print json.dumps(self.api_req)

        # print "----------TransformRequest------------"
        # print json.dumps(self.api_req, indent=2)
        # print self.api_req
        # print "--------------------------------------"

    def validate_api_req(self):

        namf.log.info("Starting validation of TransformRequest API request")

        # Check if there is a catalog loaded
        if self.api_req is not None and self.schema is not None:
            # Validate main body of request
            self.schema.validate(self.api_req)

            namf.log.debug("Main body of request validated successfully.")

            # Validate each operation individually
            for unit in self.api_req["measUnits"]:

                namf.log.debug("Validating unit {0}".format(unit["id"]))

                if "measItems" in unit.keys():
                    for item in unit["measItems"]:

                        namf.log.debug("Validating item {0}".format(item["id"]))

                        if "operations" in item.keys():
                            for operation in item["operations"]:
                                # Find schema for this item
                                if operation["type"] in self.ops_schemas["item"].keys():
                                    namf.log.debug("Validating item operation {0}".format(operation["type"]))

                                    self.ops_schemas["item"][operation["type"]].validate(operation["def"])

                if "operations" in unit.keys():
                    for operation in unit["operations"]:
                        # Find schema for this unit
                        if operation["type"] in self.ops_schemas["unit"].keys():
                            namf.log.debug("Validating unit operation {0}".format(operation["type"]))
                            self.ops_schemas["unit"][operation["type"]].validate(operation["def"])

                # No operations for this unit
                else:
                    continue
        else:
            raise ValueError("Must load catalog and define schema before validation can take place")
