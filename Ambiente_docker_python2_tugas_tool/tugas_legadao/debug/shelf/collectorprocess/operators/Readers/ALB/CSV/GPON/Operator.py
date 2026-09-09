#!/usr/bin/env python

__doc__ = \
'''
	ALB Netwin GPON Inventory Reader
'''

__version__ = '1.0'

__authors__ = [
	"Version 1.0: Paulo Gil <paulo-a-gil@alticelabs.com>"
]

import os
import csv
import importlib

# Local libraries
BaseOperator = importlib.import_module("shelf.collectorprocess.operators.BaseOperator").BaseOperator
FamilyObject = importlib.import_module("shelf.collectorprocess.operators.FamilyObject").FamilyObject
logger = importlib.import_module("shelf.collectorprocess.logger").logger

class Operator(BaseOperator):

    # Class Constructor
    def __init__(self, operationParams, baseObject={}):
        BaseOperator.__init__(self, operationParams, baseObject=baseObject)

    def process(self, familyObj=FamilyObject(), baseObject={}):
        logger.debug("Reading ALB Netwin GPON Inventory CSV file contents...", __file__)
        filePath = familyObj.getFiles()[0]
        familyObj.clearDocuments()

        # Get file name
        fileName = os.path.basename(filePath)
        familyObj.fileName = fileName

        # Try opening file in read mode
        f = None
        try:
            f = open(filePath, 'r')
        except IOError:
            logger.error(
                "Could not open sample file \"{0}\" in read mode: ".format(fileName), __file__)

        starttime = None
        unitID = None
        header = list()

        for nLine, line in enumerate(csv.reader(f, delimiter=';')):
            if not line:
                continue

            if nLine < 3:
                if not starttime:
                    starttime = line[0]
                elif not unitID:
                    unitID = line[0]
                    familyObj.setUnitID(unitID)
                elif header == list():
                    header = line
                    # Uppercase header items, just in case
                    header = [item.upper() for item in header]
                continue
            else:
                if len(header) != len(line):
                    logger.warning("Line with invalid number of fields in file '{0}'".format(familyObj.fileName))
                    continue
                try:
                    # Creates a dict from the zip between header and the current line
                    document = dict(zip(header, line))
                    document["STARTTIME"] = starttime
                    document["GRANULARITYPERIOD"] = 1440

                    try:
                        data_time = familyObj.parseEnvelopeDataTime(document["STARTTIME"])
                    except ValueError as e:
                        logger.warning("Could not build mediationEnvelope due to {0}: ".format(e), __file__)
                        continue

                    # Setting up the envelop
                    familyObj.addDocument({"dataTime": data_time, "granularitySec": document["GRANULARITYPERIOD"], "data": document})
                    self.nextOp(familyObj=familyObj, baseObject=baseObject)
                    familyObj.clearDocuments()

                except Exception as e:
                    logger.warning("Unable to process {0} in unit {1} because wrong format => {2}".format(familyObj.fileName, unitID, e), __file__)
                    continue
