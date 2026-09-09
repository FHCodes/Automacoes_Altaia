#!/usr/bin/env python


__version__ = '0.1'

__authors__ = [
    "Version 0.1: Joao Pio <joao-t-pio@telecom.pt>"
]

import json
import re
import os

# import an instance of a custom class, for logging across the different scripts
from tools.logger import namf_logger as namf

from schema import SchemaError
from schema import Schema, And, Use, Optional, Regex


class Configurations:

    # Class Constructor
    def __init__(self):

        self.clientreg = '^(.*)_client\.xml$'
        self.ossreg = '^(.*)_oss\.xml$'
        self.opsreg = '^(.*)_operations\.xml$'
        self.oidsreg = '^(.*)_oids\.xml$'

        self.schema = Schema(
            {
                "catalogsPath": Use(os.path.dirname),
                "collector": Use(str),
                Optional("client"): Regex(self.clientreg),
                Optional("oss"): Regex(self.ossreg),
                Optional("operations"): Regex(self.opsreg),
                Optional("output"): Use(str),
                Optional("outputjson"): Use(str),
                Optional("outputjson_operations"): Use(str),
                Optional("outputjson_loadinv"): Use(str),
                "catalogVersion": Use(str),
                "vendor": Use(str),
                "model": Use(str),
                Optional("deactivate"): [Use(str)],
                "units": {
                    "active": Use(str),
                    "id": Use(str),
                    "tableName": Use(str),
                    "name": Use(str),
                    "description": Use(str),
                    "tech": Use(str),
                    "udn": Use(str),
                    "measuredObjects": Use(str),
                    "granularityField": Use(str),
                    "granularityUnit": Use(str),
                    "stateOrigin": Use(str),
                    "objectType": Use(str),
                    "vendorId": Use(str),
                    "useCorrelationFields": Use(str),
                    "partitionOf": Use(str)
                },
                "items": {
                    "active": Use(str),
                    "id": Use(str),
                    "vendorId": Use(str),
                    "columnName": Use(str),
                    "type": Use(str),
                    "measItemType": Use(str),
                    "description": Use(str),
                    "name": Use(str),
                    "udn": Use(str),
                    "typeVendor": Use(str),
                    "typeCust": Use(str),
                    "unitVendor": Use(str),
                    "stateOrigin": Use(str),
                    "oid": Use(str),
                    "oidtype": Use(str)
                },
                "datasource": {
                    "defineTopic": Use(str),
                    "id": Use(str),
                    "schema": Use(str),
                    "user": Use(str),
                    "password": Use(str),
                    "isSNMP": Use(bool),
                    "destinationBasePath": Use(str)
                },
                "mongo": {
                    "datasourceId": Use(str),
                    "enrichmentId": Use(str),
                    "ip": Use(str),
                    "port": Use(int),
                    "user": Use(str),
                    "password": Use(str),
                    "db": Use(str),
                    "collection": Use(str)
                }
            })

        # General configurations
        self.gconfs = None

        self.units = None
        self.items = None
        self.datasource = None
        self.mongo = None

    # Loads the configuration file to a dictionary
    def load_configurations(self, configuration_file):

        # load the configuration file
        try:
            self.gconfs = json.load(configuration_file)
        except Exception as e:
            namf.log.critical("Could not load configurations due to {0}".format(e))
            raise Exception()

        # Validate the configurations
        try:
            self.gconfs = self.schema.validate(self.gconfs)

            # copy the subconfs
            self.units = self.gconfs["units"]
            self.items = self.gconfs["items"]
            self.datasource = self.gconfs["datasource"]
            self.mongo = self.gconfs["mongo"]

        except SchemaError as e:
            namf.log.critical("Could not validate configurations due to {0}".format(e))
            raise Exception()

        # Verify if catalog names need to be constructed
        self.gconfs["catalog_basename"] = re.sub("/", "_", self.gconfs["collector"])

        if "output" not in self.gconfs.keys():
            try:
                cmatch = re.match(self.clientreg, self.gconfs["client"])
                self.gconfs["output"] = "loading_{0}.xml".format(cmatch.group(1))
            except KeyError:
                self.gconfs["output"] = "loading_{0}.xml".format(self.gconfs["catalog_basename"])

        if "outputjson" not in self.gconfs.keys():
            try:
                cmatch = re.match(self.clientreg, self.gconfs["client"])
                self.gconfs["outputjson"] = "loading_{0}.json".format(cmatch.group(1))
            except KeyError:
                self.gconfs["outputjson"] = "loading_{0}.json".format(self.gconfs["catalog_basename"])

        if "outputjson_operations" not in self.gconfs.keys():
            try:
                opmatch = re.match(self.opsreg, self.gconfs["operations"])
                self.gconfs["outputjson_operations"] = "transform_{0}.json".format(opmatch.group(1))
            except KeyError:
                self.gconfs["outputjson_operations"] = "transform_{0}.json".format(self.gconfs["catalog_basename"])

        if "outputjson_loadinv" not in self.gconfs.keys():
            try:
                opmatch = re.match(self.opsreg, self.gconfs["operations"])
                self.gconfs["outputjson_loadinv"] = "loadinv_{0}.json".format(opmatch.group(1))
            except KeyError:
                self.gconfs["outputjson_loadinv"] = "loadinv_{0}.json".format(self.gconfs["catalog_basename"])
