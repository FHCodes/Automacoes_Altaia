#!/usr/bin/env python

__doc__ = \
'''
	ALB Netwin RAN Inventory Parameters Reader
'''

__version__ = '0.1'

__authors__ = [
	"Version 0.1: Paulo Gil <paulo-a-gil@alticelabs.com>"
]

import os
import re
import importlib
from csv import reader
from datetime import datetime

# Local libraries
BaseOperator = importlib.import_module("shelf.collectorprocess.operators.BaseOperator").BaseOperator
FamilyObject = importlib.import_module("shelf.collectorprocess.operators.FamilyObject").FamilyObject
logger = importlib.import_module("shelf.collectorprocess.logger").logger

class Operator(BaseOperator):

    # Class Constructor
    def __init__(self, operationParams, baseObject={}):
        BaseOperator.__init__(self, operationParams, baseObject=baseObject)

    def process(self, familyObj=FamilyObject(), baseObject={}):
        logger.debug("Reading ALB Netwin RAN Inventory CSV file contents...", __file__)
        filePath = familyObj.getFiles()[0]
        familyObj.clearDocuments()

        # Get file's name to find the unitID
        fileName = os.path.basename(filePath)

        # Get the unit and date from the filename
        regexFileName = re.search(r'^BDU_Altaia_?(?P<unit>\S+)?_(?P<date>\d{8}).csv$', fileName)

        unit = "NONE"
        if regexFileName.group('unit'):
            unit = regexFileName.group('unit').upper()

        # Parse and change datetime format
        startTime = '{0}000000'.format(regexFileName.group('date'))
        startTime = datetime.strptime(startTime, "%Y%m%d%H%M%S")
        startTime = datetime.strftime(startTime, "%Y-%m-%d %H:%M:%S")

        # Mapping the family names with the unit in the filename
        mapping = {"NODES": "oi_radio_nodes_inv", "NONE": "oi_radio_inv"}
        familyObj.setUnitID(mapping[unit])

        familyObj.fileName = fileName

        f = None
        try:
            # Open file for reading
            f = open(filePath, 'r')
        except IOError:
            logger.error(
                "Could not open sample file \"{0}\" in read mode: ".format(fileName), __file__)

        header = []

        for line in reader(f, delimiter=';'):

            if not line:
                continue

            line = [item.decode("latin-1") for item in line]

            # Get the first line as header and jumps to the next line
            if header == []:
                header = [item.upper() for item in line]
                continue

            if len(header) != len(line):
                logger.warning("Line with invalid number of fields in file '{0}'".format(familyObj.fileName))
                continue

            try:
                # Creates a dict from the zip between header and the current line
                document = dict(zip(header, line))
                document["STARTTIME"] = startTime

                try:
                    data_time = familyObj.parseEnvelopeDataTime(startTime)
                except ValueError as e:
                    logger.warning("Could not build mediationEnvelope due to {0}: ".format(e), __file__)
                    continue

                # Setting up the envelop
                familyObj.addDocument({"dataTime": data_time, "granularitySec": 1440, "data": document})
                self.nextOp(familyObj=familyObj, baseObject=baseObject)
                familyObj.clearDocuments()

            except Exception as e:
                logger.warning("Unable to process {0} in unit {1} because wrong format => {2}".format(familyObj.fileName, mapping[unit], e), __file__)
                continue
