#!/usr/bin/env python


__version__ = '0.1'

__authors__ = [
    "Version 0.1: Joao Pio <joao-t-pio@alticelabs.pt>"
]

# Local Libraries
import tools.parseTools as pt
import configurations as cfg
from namfRequest import LoadingRequest, TransformRequest
# import an instance of a custom class, for logging across the different scripts
from tools.logger import namf_logger as namf
from tools.catalogTools import merge_catalogs, load_catalog, merge_client_oids

# Standard Libraries
import argparse
import os
import sys
import re
import lxml.etree as et
from collections import OrderedDict
from posixpath import join

import logging
import json

# Third Party Libraries
from schema import SchemaError

# get the location of the python source file (avoids errors when running script from other folders)
PATH = os.path.dirname(os.path.abspath(__file__))


# arguments parser
def converter_parse():
    parser = argparse.ArgumentParser(description='Old catalog merger and API request producer.')

    parser.add_argument("-oj", default=os.path.join(PATH, "json"), type=pt.is_w_dir, help='json output directory')
    parser.add_argument("-ox", default=os.path.join(PATH, "xml"), type=pt.is_w_dir, help='xml output directory')

    parser.add_argument("--indir", default=os.path.join(PATH, "catalogs"), type=pt.is_r_dir,
                        help='the catalogs directory')

    parser.add_argument("--conf", default=os.path.join(PATH, "config/config.json"), type=argparse.FileType('r'),
                        help='the configuration file')

    parser.add_argument("--id", help='Sync Catalog id', default=None)

    # Behaviour flags
    parser.add_argument("-v", "--verbose", action="store_true", default=False, help='increase output verbosity')
    parser.add_argument("-d", "--debug", action="store_true", default=False,
                        help='increase output verbosity to debug mode')
    parser.add_argument("-x", "--xml", action="store_true", default=False, help='Generate XML merged catalog')
    parser.add_argument("-tf", "--transform", action="store_true", default=False, help='Generate transform JSON')
    parser.add_argument("-ld", "--loading", action="store_true", default=False, help='Generate loading JSON')
    parser.add_argument("-mp", "--measpart", action="store_true", default=False, help='Auto generate measurement partition operations')
    parser.add_argument("-da", "--deactivate", action="store", default=None,
                        help='Deactivate families from loading JSON. '
                             'Accepts "all" to deactivate all or {"tablename", "id"} to define which identifier to use for deactivating from a list'
                             'contained in the configuration file')
    parser.add_argument("-ac", "--activate", action="store", default=None,
                        help='Activate families from loading JSON. '
                             'Accepts "all" to activate all or {"tablename", "id"} to define which identifier to use for activating from a list'
                             'contained in the configuration file')
    parser.add_argument("-li", "--loadinv", action="store_true", default=False, help='Generate Loading Inventory JSON')
    parser.add_argument("-pp", "--prettyprint", action="store_true", default=False, help='Generate JSON catalogs with pretty formatting')

    arguments = parser.parse_args()

    # normalize paths
    arguments.oj = os.path.abspath(arguments.oj)
    arguments.ox = os.path.abspath(arguments.ox)
    arguments.indir = os.path.abspath(arguments.indir)

    return arguments


# Generates loading inventory creation statements
def loading_inventory(client, configurations, id):
    namf.log.info("Generating Loading Inventory catalog {0}".format(configurations.gconfs["client"]))

    loading_inv = list()

    for client_table in client["root"]["table"]:
        if configurations.datasource["isSNMP"]:
            u = {"snmpCollectedFilesPath": str(join(configurations.datasource["destinationBasePath"], "<vendor>", "<model>", str(client_table["id"].upper()), "<ip_node>", "<date>"))}
        else:
            u = dict()
        
        u.update({"catalogId": "{{ catalogID }}"} if id is None else {"catalogId": id})
        u.update({"measUnitId": str(client_table["id"].upper()),
                  "tableName": str(client_table["tableName"].upper()),
                  "schemaName": str(configurations.datasource["schema"]),
                  "datasourceId": str(configurations.datasource["id"])})
        
        if str(configurations.datasource["defineTopic"]) != "":
            u.update({"kafkaTopicId": str(configurations.datasource["defineTopic"])})

        loading_inv.append(u)

    # Build the output file
    loading_inv_json = json.dumps(loading_inv, indent=4, separators=(',', ': '))

    with open(PATH + '/json/' + configurations.gconfs["outputjson_loadinv"], "wb") as outfile:
        outfile.write(loading_inv_json)


if __name__ == "__main__":

    # Parsing stage---------------------------------------------------------
    try:
        args = converter_parse()
    except Exception as e:
        namf.log.warning("Could not parse arguments due to {0}".format(e))
        sys.exit()
    # ----------------------------------------------------------------------

    # Set logging level according to args-----------------------------------
    if args.verbose:
        # change format and increase logging level
        namf.set_level(logging.INFO)

    if args.debug:
        # change format and increase logging level
        namf.set_format(namf.FORMAT_DETAILED)
        namf.set_level(logging.DEBUG)
    # ----------------------------------------------------------------------

    # Load configurations---------------------------------------------------
    try:
        conf = cfg.Configurations()
        conf.load_configurations(args.conf)
    except Exception as e:
        namf.log.critical("Could not load the configurations due to {0}".format(e))
        sys.exit()
    # ----------------------------------------------------------------------

    namf.log.info("#######################START##################################")

    # Catalogs loading and processing stage---------------------------------
    try:
        # Check what catalog information is available
        namf.log.info("Finding catalogs corresponding to collector {0} in catalogs folder {1}/{2}".format(conf.gconfs["collector"], conf.gconfs["catalogsPath"], conf.gconfs["vendor"]))

        args.indir = os.path.join(conf.gconfs["catalogsPath"], conf.gconfs["vendor"], conf.gconfs["collector"])

        for root, dirs, files in os.walk(args.indir, topdown=False):
            for name in files:
                client_match = re.match(conf.clientreg, name)
                try:
                    if client_match.group(1) == conf.gconfs["catalog_basename"]:
                        conf.gconfs["client"] = os.path.join(root, name)
                except AttributeError:
                    pass

                operations_match = re.match(conf.opsreg, name)
                try:
                    if operations_match.group(1) == conf.gconfs["catalog_basename"]:
                        conf.gconfs["operations"] = os.path.join(root, name)
                except AttributeError:
                    pass

                oss_match = re.match(conf.ossreg, name)
                try:
                    if oss_match.group(1) == conf.gconfs["catalog_basename"]:
                        conf.gconfs["oss"] = os.path.join(root, name)
                except AttributeError:
                    pass

                oids_match = re.match(conf.oidsreg, name)
                try:
                    if oids_match.group(1) == conf.gconfs["catalog_basename"]:
                        conf.gconfs["oids"] = os.path.join(root, name)
                except AttributeError:
                    pass

        # Loads client catalog to dictionary
        namf.log.info("Loading client catalog {0}".format(os.path.join(args.indir, conf.gconfs["client"])))
        d_client = load_catalog(os.path.join(args.indir, conf.gconfs["client"]))

        # Creates list of families
        families_list = []
        for unit in d_client["root"]["table"]:
            families_list.append(unit["id"].upper())

        if args.loading:
            d_oids = None

            # Loads oss catalog to dictionary
            namf.log.info("Loading OSS catalog {0}".format(os.path.join(args.indir, conf.gconfs["oss"])))
            d_oss = load_catalog(os.path.join(args.indir, conf.gconfs["oss"]))

            # Optionally loads oids catalog to dictionary
            if "oids" in conf.gconfs.keys():
                namf.log.info("Loading OIDs catalog {0}".format(os.path.join(args.indir, conf.gconfs["oids"])))
                d_oids = load_catalog(os.path.join(args.indir, conf.gconfs["oids"]))

        # Loads operations catalog to dictionary (Optional)
        if args.transform:
            namf.log.info("Loading operations catalog {0}".format(os.path.join(args.indir, conf.gconfs["operations"])))
            d_operations = load_catalog(os.path.join(args.indir, conf.gconfs["operations"]),
                                        list_fields=['unit', 'item', 'operation', 'newField', 'item', 'fields', 'allow',
                                                     'regex', 'sharedField'])
    except Exception as e:
        namf.log.critical("Could not load catalog due to {0}. {1}. Aborting.".format(e, type(e)))
        sys.exit()

    if args.loadinv:
        try:
            # Generate the loading inventory catalog
            loading_inventory(d_client, conf, args.id)

        except Exception as e:
            namf.log.critical("Could not generate the loading inventory json due to {0}".format(e))
            sys.exit()

    if args.loading:

        if d_oids is not None:
            try:
                # Pre merge the client and oids catalogs, if the latter exists
                d_client = merge_client_oids(d_client, d_oids, conf)
            except Exception as e:
                namf.log.critical("Merge of client and oids catalogs failed due to {0}. Aborting.".format(e))
                sys.exit()

        try:
            # Merge the client and OSS catalogs
            root = merge_catalogs(d_client, d_oss, conf, args.id)
        except Exception as e:
            namf.log.critical("Merge of client and oss catalogs failed due to {0}. Aborting.".format(e))
            sys.exit()
    # ----------------------------------------------------------------------

    # Generation of XML merged catalog (Optional)---------------------------
    if args.xml and args.loading:
        # build target catalog path
        target = os.path.join(args.ox, conf.gconfs['client'].replace("_client", "_merged"))
        namf.log.info("Generating XML merged catalog {0}".format(os.path.basename(target)))
        # Convert root element to elementTree
        tree = et.ElementTree(root)

        # Write merged catalog to file
        with open(target, "wb") as file:
            namf.log.info("Writing merged catalog to {0}".format(target))
            tree.write(target, xml_declaration=True, encoding='utf-8', method="xml", pretty_print=True)
    # ----------------------------------------------------------------------

    # API Requests build and validation stage-------------------------------
    if args.loading:
        loading_request = LoadingRequest()

        # Load catalog to object by converting it to dictionary
        try:
            loading_request.load_catalog(et.tostring(root, encoding='utf-8'))
        except Exception as e:
            namf.log.critical("Could not convert catalog to dictionary due to {0}. Aborting.".format(e))
            sys.exit()

        # Validate the dictionary with a schema
        try:
            loading_request.build_api_req()
            namf.log.info("Loading catalog converted to API request")
        except Exception as e:
            namf.log.critical("Error constructing LoadingRequest API request due to {0}. Aborting.".format(e))
            sys.exit()
        try:
            loading_request.validate_api_req()
            namf.log.info("Loading API request validated")
        except ValueError as e:
            namf.log.critical("Error validating catalog due to -> {0}: {1}. Aborting.".format(e.__class__.__name__, e))
            sys.exit()
        except SchemaError as e:
            namf.log.critical("Error validating catalog due to -> {0}: {1}. Aborting.".format(e.__class__.__name__, e))
            sys.exit()

        # try:
        #     loading_request.add_origin_units()
        #     namf.log.info("Loading API adding unitSplit units")
        # except Exception as e:
        #     namf.log.critical("Error adding unitSplit units to catalog due to {0}. Aborting.".format(e))
        #     sys.exit()

        if args.deactivate is not None:
            try:
                loading_request.deactivate_from_list(conf.gconfs["deactivate"], args.deactivate)
            except KeyError:
                namf.log.warning(
                    "Error deactivating families from loading catalog due to deactivate list not present in configuration.")

        if args.activate is not None:
            try:
                loading_request.activate_from_list(conf.gconfs["activate"], "tableName")
            except KeyError:
                namf.log.warning(
                    "Error activating families from loading catalog due to activate list not present in configuration.")

        # Write loading request to file
        with open(os.path.join(args.oj, conf.gconfs["outputjson"]), "wb") as file:
            namf.log.info("Writing Loading request to {0}".format(os.path.join(args.oj, conf.gconfs["outputjson"])))
            if args.prettyprint:
                json.dump(loading_request.api_req, file, indent=4)
            else:
                json.dump(loading_request.api_req, file)

    if args.transform:

        try:
            transform_request = TransformRequest(families_list=families_list, configurations=conf)
            transform_request.load_catalog(os.path.join(args.indir, conf.gconfs["operations"]))
        except Exception as e:
            namf.log.critical("Error constructing TransformRequest due to {0}. Aborting.".format(e))
            sys.exit()

        try:
            transform_request.build_api_req(args.id)
            namf.log.info("Transform catalog converted to API request")
        except Exception as e:
            namf.log.critical("Error constructing TransformRequest API request due to {0}. Aborting.".format(e))
            sys.exit()

        # Generates measurement Partition operations automatically, based on the client catalog
        if args.measpart:
            shared_fields_dict = dict()

            for table in d_client["root"]["table"]:
                if "partitionof" in table.keys():
                    parent = table["partitionof"]
                    if parent.upper() == table["id"].upper():
                        # Same family, no need to make measurement Partition
                        continue
                    else:
                        found_parent = False

                        # Find the parent family and get list of column names to find duplicates
                        for parent_table in d_client["root"]["table"]:
                            if parent_table["id"].upper() == parent.upper():
                                found_parent = True

                                if parent_table["id"].upper() not in shared_fields_dict.keys():
                                    shared_fields_dict[parent_table["id"].upper()] = dict()

                                shared_fields = list()

                                try:
                                    for parent_column in parent_table["column"]:
                                        found_column = False
                                        for column in table["column"]:
                                            if parent_column["id"].upper() == column["id"].upper():
                                                found_column = True
                                                shared_fields.append(column["id"].upper())
                                                break
                                except KeyError:
                                    # Empty table, use ID and PK fields from daughter table
                                    for column in table["column"]:
                                        if column["dbn0type"] in ["PK", "ID"]:
                                            shared_fields.append(column["id"].upper())

                                if len(shared_fields) > 0:
                                    key = "#".join(sorted(shared_fields))

                                    if key in shared_fields_dict[parent_table["id"].upper()].keys():
                                        shared_fields_dict[parent_table["id"].upper()][key].append(table["id"].upper())
                                    else:
                                        shared_fields_dict[parent_table["id"].upper()][key] = [table["id"].upper()]

                            else:
                                continue
                else:
                    namf.log.warning("Table {0} does not have partitionof info. Skipping.".format(table["id"]))
                    continue

            # With the information gathered from the client catalog, apply operations to the transform catalog
            for unit in transform_request.api_req["measUnits"]:
                if unit["id"].upper() in shared_fields_dict:
                    # For each combination of shared fields, create a measurement partition operation
                    for key in shared_fields_dict[unit["id"].upper()].keys():
                        op = {"type": "measurementPartition", "def": [{"sharedFields": [], "measurements": []}]}

                        for field in key.split("#"):
                            op["def"][0]["sharedFields"].append(field)

                        for meas in shared_fields_dict[unit["id"].upper()][key]:
                            op["def"][0]["measurements"].append(meas)

                        if "operations" not in unit.keys():
                            unit["operations"] = [OrderedDict(op)]
                        else:
                            unit["operations"].append(OrderedDict(op))

        try:
            transform_request.validate_api_req()
            namf.log.info("Transfom API request validated")
        except ValueError as e:
            namf.log.critical("Error validating catalog due to -> {0}: {1}. Aborting.".format(e.__class__.__name__, e))
            sys.exit()
        except SchemaError as e:
            namf.log.critical("Error validating catalog due to -> {0}: {1}. Aborting.".format(e.__class__.__name__, e))
            sys.exit()

        # Write transform request to file
        with open(os.path.join(args.oj, conf.gconfs["outputjson_operations"]), "wb") as file:
            namf.log.info(
                "Writing Transform request to {0}".format(os.path.join(args.oj, conf.gconfs["outputjson_operations"])))
            if args.prettyprint:
                json.dump(transform_request.api_req, file, indent=4)
            else:
                json.dump(transform_request.api_req, file)

# ----------------------------------------------------------------------
