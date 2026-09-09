
# Third party libs
import lxml.etree as et
import xmltodict
import re

# Local libs
from logger import namf_logger as namf


# validates a catalog with a XSD schema
# def validate_XML_catalog(catalog, xsd_schema):
    # validate arguments
    # if type(catalog) !=


# loads a xml catalog to a dictionary
def load_catalog(catalog_path, list_fields=None):

    if list_fields is None:
        list_fields = ['table', 'column', 'unit', 'item']
    with open(catalog_path) as catfile:
        return xmltodict.parse(catfile.read(), attr_prefix='', force_list=list_fields)


# Merge client and oss catalogs
def merge_catalogs(client, oss, configurations, id):
    # Create Unified Loading catalog dictionary to check for duplicates
    ul_dict = {}

    # Create root node
    if id is None:
        root = et.Element("root", version=configurations.gconfs['catalogVersion'], id="{{ catalogID }}")
    else:
        root = et.Element("root", version=configurations.gconfs['catalogVersion'], id=id)

    # Loop all client catalog's tables
    for table in client['root']['table']:

        u = table.get('id')

        # Create measUnits node
        new_meas_unit = et.SubElement(root, "measUnits")

        namf.log.debug("<measUnit>")

        # Loop all oss catalog's units
        for unit in oss['root']['unit']:
            try:
                # Table (client) is the same as Unit (OSS)
                if table.get('ossId').upper() == unit.get('ossId').upper():

                    namf.log.debug("table.get('ossId').upper():{0} == unit.get('ossId').upper():{1}".format(
                        table.get('ossId').upper(), unit.get('ossId').upper()))

                    if table.get('id').upper() in ul_dict.keys():
                        namf.log.critical(
                            "Detected duplicated table {0} in the client catalog. Client must be fixed.".format(
                                table.get("id")))
                        break
                    else:
                        # print "add {0}".format(table.get('id').upper())
                        ul_dict[table.get('id').upper()] = {}

                    # remap unit attributes ids according to conf.json
                    for new, old_att in configurations.gconfs['units'].items():
                        
                        # split old by ";" to accept a list of possible xml attributes, instead of only one static
                        old_list = [at.strip() for at in old_att.split(";")]
                        accepted = False
                        
                        for idx, old in enumerate(old_list):
                            if accepted:
                                break
                                
                            # if the old value is a constant, add the attribute with the constant as value
                            if 'constant:' in old:
                                new_meas_unit.set(new, old.replace('constant:', ''))
                                accepted = True
                                continue
                                
                            # Add attribute from client catalog (if in conf.json)
                            if old in table.keys():
                                if old in ["udn", "desc", "name"]:
                                    new_meas_unit.set(new, str(table[old]))
                                else:
                                    new_meas_unit.set(new, str(table[old].upper()))
                                namf.log.debug("new:table[old] = {0}:{1}".format(new, table[old].upper()))
                                accepted = True
                                
                            # Add attribute from oss catalog (if in conf.json)
                            elif old in unit.keys():
                                if old in ["udn", "desc", "name"]:
                                    new_meas_unit.set(new, str(unit[old]))
                                else:
                                    new_meas_unit.set(new, str(unit[old].upper()))
                                namf.log.debug("new:unit[old] = {0}:{1}".format(new, unit[old].upper()))
                                accepted = True
                            
                            # Attribute not found but will check list if a ";" separated string was provided
                            elif not accepted and idx == len(old_list) - 1:
                                namf.log.warning(
                                    "Could not find attribute {0} in either client or oss catalog for family {1}".format(
                                        str(old_list), table.get('id')))

                    # No need to keep looping
                    break

            except KeyError as e:
                namf.log.error("Could not map UNIT old key with new key due to {0}.".format(e))
                raise KeyError(e.message)
            except AttributeError as e:
                namf.log.error("Could not map UNIT old key with new key due to {0}.".format(e))
                raise AttributeError(e.message)

        # If the node is empty, add information from the client catalog only and throw a warning
        if len(new_meas_unit.items()) == 0:
            namf.log.critical("Could not find table {0} in the OSS catalog. OSS must be fixed.".format(table.get("id")))

        # Loop all client catalog's columns for this table
        try:
            for column in table['column']:

                # Create measItems subnode
                new_meas_item = et.SubElement(new_meas_unit, "measItems")

                namf.log.debug("<measItem>")

                # Loop all oss catalog's items
                for item in unit['item']:
                    try:

                        # Column (client) is the same as Item (OSS)
                        if column.get('id').upper() == item.get('id').upper():

                            namf.log.debug(
                                "column.get('id'):{0} == item.get('id'):{1}".format(column.get('id'), item.get('id')))

                            # remap unit attributes ids according to conf.json
                            for new, old in configurations.gconfs['items'].items():

                                # if the old value is a constant, add the attribute with the constant as value
                                if 'constant:' in old:
                                    old = old.replace('constant:', '')
                                    new_meas_item.set(new, str(old))
                                # Add attribute from client catalog (if in conf.json)
                                elif old in column.keys():
                                    if old in ["udn", "desc", "name", "oid"]:
                                        new_meas_item.set(new, str(column[old]))
                                    else:
                                        new_meas_item.set(new, str(column[old].upper()))
                                    namf.log.debug("new:column[old] = {0}:{1}".format(new, column[old]))
                                # Add attribute from oss catalog (if in conf.json)
                                elif old in item.keys():
                                    if old in ["udn", "desc", "name"]:
                                        new_meas_item.set(new, str(item[old]))
                                    else:
                                        new_meas_item.set(new, str(item[old].upper()))
                                    namf.log.debug("new:item[old] = {0}:{1}".format(new, item[old]))
                                else:
                                    if old in ["oid", "oidtype"]:
                                        pass
                                    else:
                                        namf.log.warning(
                                            "Could not find attribute {0} in either client or oss catalog for family {1}, item {2}".format(
                                                old, table.get('id'), column.get('id')))

                            # No need to keep looping
                            break

                    except KeyError as e:
                        namf.log.error("Could not map ITEM old key with new key due to {0}.".format(e))

                # If the node is empty, add information from the client catalog only and throw a warning
                if len(new_meas_item.items()) == 0:
                    namf.log.critical(
                        "Could not find column {0} of table {1} in the OSS catalog. OSS must be fixed.".format(
                            column.get("id"), table.get('id')))
        except KeyError as e:
            namf.log.warning("Empty table with id {0} detected.".format(u))

            # Create measItems subnode
            new_meas_item = et.SubElement(new_meas_unit, "measItems")

            namf.log.debug("<measItem>")

    return root


def merge_client_oids(client, oids, configurations):

    oid_regex = re.compile("^\.\d[\.\d]*(<id>)?$")

    # Loop all client catalog's tables
    for table in client['root']['table']:
        table_id = table.get('id')

        # Loop all oids catalog's units
        for unit in oids['root']['unit']:
            try:
                # Table (client) is the same as Unit (OSS)
                if table.get('id').upper() == unit.get('id').upper():

                    namf.log.debug("merge_client_oids - table.get('id').upper():{0} == unit.get('id').upper():{1}".format(
                        table.get('id').upper(), unit.get('id').upper()))

                    # Loop all oids catalog's items
                    for item in unit['item']:
                        item_name = item.get('name')
                        for column in table["column"]:
                            column_id = column.get('id')

                            if column_id.upper() == item_name.upper():
                                if oid_regex.match(item["oid"]) is None:
                                    raise ValueError("OID does not conform to expected format: {0}".format(item["oid"]))
                                column["oid"] = item["oid"]
                                column["oidtype"] = item["type"]

            except KeyError as e:
                namf.log.error("merge_client_oids - Could not map UNIT old key with new key due to {0}.".format(e))
                raise KeyError(e.message)
            except AttributeError as e:
                namf.log.error("merge_client_oids - Could not map UNIT old key with new key due to {0}.".format(e))
                raise AttributeError(e.message)
            except ValueError as e:
                raise ValueError(e.message)

    return client