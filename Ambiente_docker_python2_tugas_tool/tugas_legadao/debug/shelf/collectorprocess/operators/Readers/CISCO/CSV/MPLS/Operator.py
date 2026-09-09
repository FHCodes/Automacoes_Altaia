#!/usr/bin/env python

__doc__ = \
    '''
    CISCO MPLS Reader
'''

__version__ = '2.0'

__authors__ = [
    "Version 1.0: Marco Jeronimo <marco-a-jeronimo@alticelabs.com>"
    "Version 2.0: Marco Jeronimo <marco-a-jeronimo@alticelabs.com>"
]

import copy
import re
import os
import csv
import time
import importlib

# Local libraries
BaseOperator = importlib.import_module("shelf.collectorprocess.operators.BaseOperator").BaseOperator
FamilyObject = importlib.import_module("shelf.collectorprocess.operators.FamilyObject").FamilyObject
logger = importlib.import_module("shelf.collectorprocess.logger").logger


class Operator(BaseOperator):

    # Class Constructor
    def __init__(self, operationParams, baseObject={}):
        BaseOperator.__init__(self, operationParams, baseObject=baseObject)
        self.MAX_DUPLICATE_WARNINGS = 100
        self.duplicateWarnings = 0

        self.name_regex = re.compile("^PPM_(.*?)_(?P<FAMILY>.*)_\.(?P<DATETIME>.*)\.csv.*$")

    def process(self, familyObj=FamilyObject(), baseObject={}):

        SUB_INTF_CORE_STATS_header = ["TIMESTAMP", "GRANULARITYPRD", "NODE", "SUBINTERFACENAME", "SUBINTERFACEDESC",
                                      "TRAFFIC_IN_OCTETS", "TRAFFIC_OUT_OCTETS", "INTERFACESPEED",
                                      "TRAFFIC_IN_DISCARDED_PACKETS", "TRAFFIC_IN_ERRORS_PACKETS",
                                      "TRAFFIC_OUT_DISCARDED_PACKETS", "TRAFFIC_OUT_ERRORS_PACKETS", "TYPE", "VRF_NAME",
                                      "INTERFACE_ID", "SUBINTF_ID", "INTF_NAME", "INTERVAL"]
        COS_NETWORK_STATS_header = ["TIMESTAMP", "GRANULARITYPRD", "NODE", "SUBINTERFACENAME", "SUBINTERFACEDESC",
                                    "CLASS_OF_SERVICE", "POLICY_MAP", "COS_DIRECTION", "COS_TRAFFIC_IN",
                                    "COS_TRAFFIC_OUT", "COS_TRAFFIC_OUT_DISCARDED", "INTERFACE_ID", "SUBINTF_ID",
                                    "INTF_NAME", "TYPE", "INTERVAL"]
        SUB_INTF_SERVICE_STATS_header = ["TIMESTAMP", "GRANULARITYPRD", "NODE", "SUBINTERFACENAME", "SUBINTERFACEDESC",
                                         "VRF_NAME", "ATM_VCI", "ATM_VPI", "ATM_CRCERROR", "ATM_OVERSIZEDSDU",
                                         "ATM_SARTIMEOUT", "TRAFFIC_IN_OCTETS", "TRAFFIC_OUT_OCTETS", "INTERFACESPEED",
                                         "TRAFFIC_IN_DISCARDED_PACKETS", "TRAFFIC_IN_ERRORS_PACKETS",
                                         "TRAFFIC_OUT_DISCARDED_PACKETS", "TRAFFIC_OUT_ERRORS_PACKETS", "TYPE",
                                         "INTERFACE_ID", "SUBINTF_ID", "INTF_NAME", "INTERVAL"]
        COS_SERVICE_STATS_header = ["TIMESTAMP", "GRANULARITYPRD", "NODE", "SUBINTERFACENAME", "SUBINTERFACEDESC",
                                    "VRF_NAME", "ATM_VCI", "ATM_VPI", "ATM_CRCERROR", "ATM_OVERSIZEDSDU",
                                    "ATM_SARTIMEOUT", "CLASS_OF_SERVICE", "POLICY_MAP", "COS_DIRECTION",
                                    "COS_TRAFFIC_IN",
                                    "COS_TRAFFIC_OUT", "COS_TRAFFIC_OUT_DISCARDED", "INTERFACE_ID", "SUBINTF_ID",
                                    "INTF_NAME", "CUSTOMER_ID", "SERVICE_ID", "TYPE", "INTERVAL"]

        logger.debug("[Reader] Reading CISCO MPLS CSV files' contents...", __file__)
        filesToProcess = familyObj.getFiles()

        for filePath in filesToProcess:
            familyObj.clearDocuments()
            self.duplicateWarnings = 0

            # obtem o nome do ficheiro sem o path
            fileName = os.path.basename(filePath)
            familyObj.fileName = fileName

            lista_primarykeys_service = dict()
            lista_primarykeys_core = dict()
            unitID = ""

            # valida se o ficheiro esta vazio
            if os.path.getsize(filePath) == 0:
                logger.warning("File {0} is empty.".format(filePath), __file__)
                continue

            try:
                f = open(filePath, 'r')
            except IOError:
                logger.error("Could not open sample file \"{0}\" in read mode: ".format(fileName), __file__)
                continue

            if "EntSensors" in fileName:
                unitID = "ENTSENSORS"
                familyObj.setUnitID(unitID)
            else:
                try:
                    validateRegex = self.name_regex.match(familyObj.fileName)
                    unitID = validateRegex.group("FAMILY").replace("NoSFP", "").upper()
                    familyObj.setUnitID(unitID)
                except Exception as e:
                    logger.warning("Filename not expected \"{0}\" ".format(fileName))
                    continue

            # Pode ficar mais a baixo
            if unitID == "CORE_STATS":
                familyObj.setUnitID("COS_NETWORK_STATS")
                familyObj2 = FamilyObject()
                familyObj2.fileName = fileName
                familyObj2.setUnitID("SUB_INTF_CORE_STATS")

            if unitID == "QOS_STATS":
                familyObj2 = FamilyObject()
                familyObj2.fileName = fileName

            num_docs_send = 10
            new_family_1 = ""

            header = list()
            try:
                for nLine, line in enumerate(csv.reader(f, delimiter=',', quotechar='|')):
                    # CSV Header
                    if nLine == 0:
                        if len(line) > 0:
                            # Store column names into a list
                            header = [name.upper().strip() for name in line]

                        else:
                            logger.error("Could not retrieve column names from first row of sample '{0}'".format(
                                familyObj.fileName), __file__)
                            break
                    else:
                        # Checks if number of values in row is the same as the announced columns in the header
                        if len(header) != len(line):
                            logger.warning(
                                "Line with invalid number of fields in file '{0}'".format(familyObj.fileName))
                            continue

                        line = [item.replace('"', '').decode('unicode_escape').encode('ascii', 'ignore').strip()
                                for item in line]
                        try:
                            document = dict(zip(header, line))

                            date = document["TIMESTAMP"]
                            year = date[6:10]
                            month = date[:2]
                            day = date[3:5]
                            hour = date[11:]
                            document["TIMESTAMP"] = year + "-" + month + "-" + day + " " + hour + ":00"
                            document["GRANULARITYPRD"] = int(
                                time.mktime(time.strptime(document["TIMESTAMP"], '%Y-%m-%d %H:%M:%S')))
                            document["INTERVAL"] = 15

                            if unitID == 'ENTSENSORS':
                                if document.has_key("SENSORNAME"):
                                    if document.has_key("SENSORVALUE") and "capacity" in document["SENSORNAME"] \
                                            and "PM" in document["SENSORNAME"]:
                                        document["WATTAGE_CAPACITY"] = document["SENSORVALUE"]

                                    if (document.has_key("SENSORVALUE") and "PEM Iout P" in document["SENSORNAME"]
                                    ) or (document.has_key("SENSORVALUE") and "current" in document["SENSORNAME"]
                                          and "PM" in document["SENSORNAME"]):
                                        document["CURRENT"] = document["SENSORVALUE"]

                                    if (document.has_key("SENSORVALUE") and "PEM Vout P" in document["SENSORNAME"]) or (
                                            document.has_key("SENSORVALUE") and "voltage" in document["SENSORNAME"]
                                            and "PM" in document["SENSORNAME"]):
                                        document["VOLTAGE"] = document["SENSORVALUE"]

                                    if document.has_key("SENSORVALUE") and "PEM Vin P" in document["SENSORNAME"]:
                                        document["ENTRY_VOLTAGE"] = document["SENSORVALUE"]

                                    if ("capacity" in document["SENSORNAME"] or "current" in document[
                                        "SENSORNAME"] or "voltage" in document["SENSORNAME"]) and "PM" in document[
                                        "SENSORNAME"]:
                                        document["PM_NAME"] = document["SENSORNAME"].split("/")[1]
                                        document["PM_ID"] = document["NODE"] + "/" + document["PM_NAME"]

                                    if "PEM Iout P" in document["SENSORNAME"] or "PEM Vout P" in document["SENSORNAME"]:
                                        document["PM_NAME"] = "PEM" + document["SENSORNAME"].split("/")[0].replace(
                                            "PEM Iout P", "").replace("PEM Vout P", "")
                                        document["PM_ID"] = document["NODE"] + "/" + document["PM_NAME"]

                            if unitID == "CORE_STATS":
                                document2 = dict(document)
                                for key in document2.keys():
                                    if key not in SUB_INTF_CORE_STATS_header:
                                        document2.pop(key, None)
                                for key in document.keys():
                                    if key not in COS_NETWORK_STATS_header:
                                        document.pop(key, None)

                                tempprimarykey = "SUB_INTF_CORE_STATS" + ';' + document2["TIMESTAMP"] + ';' \
                                                 + document2["NODE"] + ';' + document2["SUBINTERFACENAME"]

                                if tempprimarykey not in lista_primarykeys_core:
                                    lista_primarykeys_core[tempprimarykey] = familyObj2.fileName

                                    try:
                                        data_time = familyObj2.parseEnvelopeDataTime(document2["TIMESTAMP"])
                                        granularity_sec = familyObj2.parseEnvelopeGranularitySec(
                                            int(document2["INTERVAL"]))
                                    except ValueError as e:
                                        logger.warning("Could not build mediationEnvelope due to {0}: ".format(e), __file__)
                                        continue

                                    # Setting up the envelope
                                    familyObj2.addDocument(
                                        {"dataTime": data_time, "granularitySec": granularity_sec, "data": document2})
                                    if nLine % num_docs_send == 0:
                                        self.nextOp(familyObj=familyObj2, baseObject=baseObject)
                                        familyObj2.clearDocuments()

                            if unitID == "QOS_STATS":
                                if not document.has_key("CUSTOMER_ID") and document.has_key("VRF_NAME"):
                                    document["CUSTOMER_ID"] = document["VRF_NAME"]

                                if not document.has_key("SERVICE_ID") and document.has_key("VRF_NAME"):
                                    document["SERVICE_ID"] = document["VRF_NAME"]

                                document2 = dict(document)
                                document3 = dict(document)
                                document4 = dict(document)

                                for key in document.keys():
                                    if key not in COS_NETWORK_STATS_header:
                                        document.pop(key, None)
                                for key in document2.keys():
                                    if key not in SUB_INTF_CORE_STATS_header:
                                        document2.pop(key, None)
                                for key in document3.keys():
                                    if key not in SUB_INTF_SERVICE_STATS_header:
                                        document3.pop(key, None)
                                for key in document4.keys():
                                    if key not in COS_SERVICE_STATS_header:
                                        document4.pop(key, None)

                                if document["TYPE"] == "CORE":

                                    new_family_1 = "COS_NETWORK_STATS"

                                    if (familyObj2.getUnitID() is not None and familyObj2.getUnitID() != "SUB_INTF_CORE_STATS") or nLine % num_docs_send == 0:
                                        self.nextOp(familyObj=familyObj2, baseObject=baseObject)
                                        familyObj2.clearDocuments()

                                    familyObj2.setUnitID("SUB_INTF_CORE_STATS")

                                    tempprimarykey = "SUB_INTF_CORE_STATS" + ';' + document2["TIMESTAMP"] + ';' \
                                                     + document2["NODE"] + ';' + document2["SUBINTERFACENAME"]

                                    if tempprimarykey not in lista_primarykeys_core:
                                        lista_primarykeys_core[tempprimarykey] = familyObj2.fileName

                                        try:
                                            data_time = familyObj2.parseEnvelopeDataTime(document2["TIMESTAMP"])
                                            granularity_sec = familyObj2.parseEnvelopeGranularitySec(
                                                int(document2["INTERVAL"]))
                                        except ValueError as e:
                                            logger.warning("Could not build mediationEnvelope due to {0}: ".format(e),__file__)
                                            continue

                                        # Setting up the envelope
                                        familyObj2.addDocument(
                                            {"dataTime": data_time, "granularitySec": granularity_sec, "data": document2})

                                else:
                                    new_family_1 = "COS_SERVICE_STATS"

                                    document = copy.deepcopy(document4)

                                    if (familyObj2.getUnitID() is not None and  familyObj2.getUnitID() != "SUB_INTF_SERVICE_STATS") or nLine % num_docs_send == 0:
                                        self.nextOp(familyObj=familyObj2, baseObject=baseObject)
                                        familyObj2.clearDocuments()

                                    familyObj2.setUnitID("SUB_INTF_SERVICE_STATS")

                                    tempprimarykey = "SUB_INTF_SERVICE_STATS" + ';' + document3["TIMESTAMP"] + ';' + \
                                                    document3["NODE"] + ';' + document3["SUBINTERFACENAME"]
                                    if tempprimarykey not in lista_primarykeys_service:
                                        lista_primarykeys_service[tempprimarykey] = familyObj.fileName

                                        try:
                                            data_time = familyObj2.parseEnvelopeDataTime(document3["TIMESTAMP"])
                                            granularity_sec = familyObj2.parseEnvelopeGranularitySec(
                                                int(document3["INTERVAL"]))
                                        except ValueError as e:
                                            logger.warning("Could not build mediationEnvelope due to {0}: ".format(e),__file__)
                                            continue

                                        # Setting up the envelope
                                        familyObj2.addDocument(
                                            {"dataTime": data_time, "granularitySec": granularity_sec,
                                            "data": document3})

                                    else:
                                        if self.duplicateWarnings < self.MAX_DUPLICATE_WARNINGS:
                                            logger.warning("An pk repeat was detected in file \"{0}\" a=\"{1}\"".format(
                                                familyObj.fileName, tempprimarykey))
                                            logger.warning(
                                                "the past file with this pk is \"{0}\" ".format(lista_primarykeys_service[tempprimarykey]))
                                            self.duplicateWarnings += 1
                                            if self.duplicateWarnings >= self.MAX_DUPLICATE_WARNINGS:
                                                logger.warning("Suppressing future warnings of this nature...")

                            try:
                                data_time = familyObj.parseEnvelopeDataTime(document["TIMESTAMP"])
                                granularity_sec = familyObj.parseEnvelopeGranularitySec(
                                    int(document["INTERVAL"]))
                            except ValueError as e:
                                logger.warning("Could not build mediationEnvelope due to {0}: ".format(e), __file__)
                                continue

                            if unitID != "QOS_STATS":
                                # Setting up the envelope
                                familyObj.addDocument(
                                    {"dataTime": data_time, "granularitySec": granularity_sec, "data": document})

                                if nLine % num_docs_send == 0:
                                    self.nextOp(familyObj=familyObj, baseObject=baseObject)
                                    familyObj.clearDocuments()
                            else:
                                if (familyObj.getUnitID() != "QOS_STATS" and familyObj.getUnitID() != new_family_1) or nLine % num_docs_send == 0:
                                    self.nextOp(familyObj=familyObj, baseObject=baseObject)
                                    familyObj.clearDocuments()

                                familyObj.setUnitID(new_family_1)
                                familyObj.addDocument({"dataTime": data_time, "granularitySec": granularity_sec, "data": document})


                        except Exception as e:
                            logger.warning("Unable to process {0} in unit {1} because wrong format => {2}".format(
                                familyObj.fileName, unitID, e), __file__)
                            continue

                if unitID in ("CORE_STATS", "QOS_STATS"):
                    # Flush the remaining events by familyObj2
                    self.nextOp(familyObj=familyObj2, baseObject=baseObject)
                    familyObj2.clearDocuments()

                # Flush the remaining events by familyObj
                self.nextOp(familyObj=familyObj, baseObject=baseObject)
                familyObj.clearDocuments()

            except csv.Error as e:
                logger.warning("{0} in line {1} of file {2}".format(e, nLine, familyObj.fileName))
