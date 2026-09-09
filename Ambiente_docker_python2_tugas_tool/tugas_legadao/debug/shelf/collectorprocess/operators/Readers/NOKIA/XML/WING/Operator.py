#!/usr/bin/env python

__version__ = '1.0'

__doc__ = '''
NOKIA IMS WING Performance XML Reader
'''

__authors__ = [
	"Version 1.0: paulo-a-gil <paulo-a-gil@alticelabs.com>"
]

import os
import re
import time
import importlib
from datetime import datetime
import xml.etree.ElementTree as ET

# Local libraries
BaseOperator = importlib.import_module("shelf.collectorprocess.operators.BaseOperator").BaseOperator
FamilyObject = importlib.import_module("shelf.collectorprocess.operators.FamilyObject").FamilyObject
logger = importlib.import_module("shelf.collectorprocess.logger").logger

class Operator(BaseOperator):

    # Class constructor
    def __init__(self, operationParams, baseObject={}):
        BaseOperator.__init__(self, operationParams, baseObject=baseObject)

    def process(self, familyObj=FamilyObject(), baseObject={}):

        logger.debug("Reading NOKIA IMS WING Performance XML file' contents...", __file__)
        filePath = familyObj.getFiles()[0]

        familyObj.clearDocuments()

        fileName = os.path.basename(filePath)

        # If file is empty, bota fora :)
        if os.path.getsize(filePath) == 0:
                logger.warning("File {0} is empty.".format(fileName), __file__)
                return

        mapping = {"APN": "WING_APN", "RX_BYTES": "WING_MNO", "TX_BYTES": "WING_MNO", "PORTAL": "WING_PORTALANDMANAGEMENT", "VPN": "WING_VPN", "PORT": "WING_PORT"}
        familyObj.fileName = fileName

        try:
            # Parse File
            # Assuming spaces are gone, otherwise it will crash :(
            # <Time stamp></Time stamp>
            # <Total Kbytes></Total Kbytes>
            tree = ET.parse(filePath)
            xml = tree.getroot()
        except IOError:
            logger.error(
				"Could not open sample file \"{0}\" in read mode: ".format(fileName), __file__)
        try:
            for element in xml.findall("element"):
                document = dict()
                for obj in element:
                    document[obj.tag.upper()] = obj.text

                # Convert timestamp
                document['TIMESTAMP'] = datetime.strptime(document['TIMESTAMP'], "%d/%m/%Y %H:%M:%S")
                document['TIMESTAMP'] = datetime.strftime(document['TIMESTAMP'], "%Y-%m-%d %H:%M:%S")

                try:
                    timestamp = familyObj.parseEnvelopeDataTime(document["TIMESTAMP"])
                except ValueError as e:
                    logger.warning("Could not build mediationEnvelope due to {0}: ".format(e), __file__)
                    continue

                for key in document.keys():
                    if key in mapping.keys():
                        familyObj.setUnitID(mapping[key])
                        break

                # granularity = 15min
                familyObj.addDocument({"dataTime": timestamp, "granularitySec": 900, "data": document})
                self.nextOp(familyObj=familyObj, baseObject=baseObject)
                familyObj.clearDocuments()
        except Exception as e:
            logger.warning("Unable to process {0} due to {1}: ".format(familyObj.fileName, e), __file__)
