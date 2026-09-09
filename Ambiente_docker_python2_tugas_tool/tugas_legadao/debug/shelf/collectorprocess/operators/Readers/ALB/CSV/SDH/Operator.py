#!/usr/bin/env python

__doc__ = \
    '''
	ALB AGORA SDH Reader
'''

__version__ = '1.0'

__authors__ = [
    "Version 1.0: Marco Jeronimo <marco-a-jeronimo@alticelabs.com>"
]

import gzip
import io
import re
from csv import reader, Sniffer
import os
import csv
import importlib
from datetime import datetime

# Local libraries
BaseOperator = importlib.import_module("shelf.collectorprocess.operators.BaseOperator").BaseOperator
FamilyObject = importlib.import_module("shelf.collectorprocess.operators.FamilyObject").FamilyObject
logger = importlib.import_module("shelf.collectorprocess.logger").logger


class Operator(BaseOperator):

    # Class Constructor
    def __init__(self, operationParams, baseObject={}):
        BaseOperator.__init__(self, operationParams, baseObject=baseObject)

        self.name_regex = re.compile("^sdh_(?P<FAMILY>[^_]+)\_(?P<DATETIME>[^.]+)\.csv.*$")

    def process(self, familyObj=FamilyObject(), baseObject={}):
        logger.debug("Reading ALB AGORA SDH CSV file contents...", __file__)
        filesToProcess = familyObj.getFiles()

        for filePath in filesToProcess:
            familyObj.clearDocuments()

            # obtem o nome do ficheiro sem o path
            fileName = os.path.basename(filePath)
            familyObj.fileName = fileName

            # valida se o ficheiro esta vazio
            if os.path.getsize(filePath) == 0:
                logger.warning("File {0} is empty.".format(filePath), __file__)
                continue

            try:
                # If file is compressed, open with a buffered stream
                if os.path.splitext(filePath)[1] == ".gz":
                    f = io.BufferedReader(gzip.open(filePath))
                else:
                    f = open(filePath, 'r')
            except IOError:
                logger.error("Could not open sample file \"{0}\" in read mode: ".format(fileName), __file__)
                continue

            try:
                validateRegex = self.name_regex.match(familyObj.fileName)
                unitID = "sdh_" + validateRegex.group("FAMILY")
                familyObj.setUnitID(unitID)
            except Exception as e:
                logger.warning("Filename not expected \"{0}\" ".format(fileName))
                continue

            header = list()
            try:
                for nLine, line in enumerate(csv.reader(f, delimiter=';')):
                    # CSV Header
                    if nLine == 0:
                        # Fix name of first element of row that has a # character attached
                        if len(line) > 0:
                            line[0] = line[0].strip("#")

                            # Store column names into a list
                            header = [name.upper() for name in line]

                        else:
                            logger.error("Could not retrieve column names from first row of sample '{0}'".format(
                                familyObj.fileName), __file__)
                            break
                    else:
                        if len(header) != len(line):
                            logger.warning(
                                "Line with invalid number of fields in file '{0}'".format(familyObj.fileName))
                            continue
                        try:
                            document = dict(zip(header, line))
                            if unitID == 'sdh_enrich':
                                line = [item.decode("latin-1") for item in line]
                                document = dict(zip(header, line))
                                document["GRANULARITYPERIOD"] = 1440

                                validateRegex = self.name_regex.match(familyObj.fileName)
                                date = validateRegex.group("DATETIME")

                                document["DATETIME"] = datetime.strptime(date,
                                                                         "%Y%m%d%H%M")
                                document["DATETIME"] = datetime.strftime(document["DATETIME"],
                                                                         "%Y-%m-%d %H:%M:%S")

                                try:
                                    data_time = familyObj.parseEnvelopeDataTime(document["DATETIME"])
                                    granularity_sec = familyObj.parseEnvelopeGranularitySec(
                                        int(document["GRANULARITYPERIOD"]))
                                except ValueError as e:
                                    logger.warning("Could not build mediationEnvelope due to {0}: ".format(e), __file__)
                                    continue
                            else:
                                document["GRANULARITYPERIOD"] = 900
                                # Parse DATETIME
                                document["DATA_HORA_INICIO"] = datetime.strptime(document["DATA_HORA_INICIO"],
                                                                                 "%Y-%m-%d %H:%M")
                                document["DATA_HORA_INICIO"] = datetime.strftime(document["DATA_HORA_INICIO"],
                                                                                 "%Y-%m-%d %H:%M:%S")

                                try:
                                    data_time = familyObj.parseEnvelopeDataTime(document["DATA_HORA_INICIO"])
                                    granularity_sec = familyObj.parseEnvelopeGranularitySec(
                                        int(document["GRANULARITYPERIOD"]))
                                except ValueError as e:
                                    logger.warning("Could not build mediationEnvelope due to {0}: ".format(e), __file__)
                                    continue

                            # Setting up the envelop
                            familyObj.addDocument(
                                {"dataTime": data_time, "granularitySec": granularity_sec, "data": document})
                            self.nextOp(familyObj=familyObj, baseObject=baseObject)
                            familyObj.clearDocuments()

                        except Exception as e:
                            logger.warning("Unable to process {0} in unit {1} because wrong format => {2}".format(
                                familyObj.fileName, unitID, e), __file__)
                            continue

            except csv.Error as e:
                logger.warning("{0} in line {1} of file {2}".format(e, nLine, familyObj.fileName))
