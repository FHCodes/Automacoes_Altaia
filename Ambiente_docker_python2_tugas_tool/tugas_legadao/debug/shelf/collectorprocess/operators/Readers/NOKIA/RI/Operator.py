__version__ = '1.0'

__doc__ = '''
    NOKIA NFMT TRANS PoTN Inventory RI Reader
'''

__authors__ = [
	"Version 1.0: paulo-a-gil <paulo-a-gil@alticelabs.com>"
]

import re
import os
import json
import csv
import importlib
from datetime import datetime

# Local libraries
BaseOperator = importlib.import_module("shelf.collectorprocess.operators.BaseOperator").BaseOperator
FamilyObject = importlib.import_module("shelf.collectorprocess.operators.FamilyObject").FamilyObject
logger = importlib.import_module("shelf.collectorprocess.logger").logger

class Operator(BaseOperator):

    # Class constructor
    def __init__(self, operationParams, baseObject={}):
        BaseOperator.__init__(self, operationParams, baseObject=baseObject)

    def process(self, familyObj=FamilyObject(), baseObject={}):
        logger.debug("Reading NOKIA NFMT TRANS POTN Inventory JSON file' contents...", __file__)
        filesToProcess = familyObj.getFiles()
        familyObj.clearDocuments()

        for filePath in filesToProcess:
            familyObj.clearDocuments()

            fileName = os.path.basename(filePath)
            familyObj.fileName = fileName

            # If file is empty, bota fora :)
            if os.path.getsize(filePath) == 0:
                logger.warning("File {0} is empty.".format(fileName), __file__)
                continue

            # Try opening the file
            f = None
            try:
                f = open(filePath, "r")
            except IOError:
                logger.error("Could not open file \"{0}\" in read mode.".format(fileName), __file__)

            # Get datetime from filename
            fileNameRegex = re.match("^.*__(?P<DATETIME>.+?).ri$", fileName)
            fileNameDatetime = fileNameRegex.group("DATETIME")
            fileNameDatetime = datetime.strftime(datetime.strptime(fileNameRegex.group("DATETIME"), "%Y%m%d%H%M"), "%Y-%m-%d %H:%M:%S")

            # Set unit ID
            familyObj.setUnitID("DISC_POTN_INVENTORY_INFO")

            # Init variables
            nLine = 0
            document = dict()

            try:
                # Loop through lines of current file
                for line in f:
                    # Get counter name and value from current line
                    lineRegex = re.match("^(?P<COUNTER>.+?)\s*:\s*(?P<VALUE>.+?)$", line)

                    # If regex matches, process counter name and value
                    if lineRegex:
                        counterName = lineRegex.group("COUNTER").replace(" ","").replace("(00)","").replace("ALCATEL-LUCENT","").upper()
                        counterValue = lineRegex.group("VALUE").replace(" ","")

                        # Skip first line if exists
                        if "UPLOADREMOTE" in counterName:
                            continue

                        # Format MANUFACTURINGDATE
                        if counterName == "DATE":
                            counterName = "MANUFACTURINGDATE"

                        # If counter name is USERLABEL process document
                        elif counterName == "USERLABEL":
                            if len(document) != 0:
                                # Set DATETIME and GRANULARITY
                                document["DATETIME"] = fileNameDatetime
                                document["GRANULARITY"] = 60*24

                                # Parse envelope data time
                                try:
                                    datatime = familyObj.parseEnvelopeDataTime(document["DATETIME"])
                                except ValueError as e:
                                    logger.warning("Could not build mediationEnvelope due to {0}: ".format(e), __file__)
                                    continue

                                # Proceed with envelope
                                familyObj.addDocument({"dataTime": datatime, "granularitySec": int(document["GRANULARITY"] * 60), "data": document})
                                self.nextOp(familyObj=familyObj, baseObject=baseObject)
                                familyObj.clearDocuments()

                                # Clear document variable
                                document = dict()

                        # Add counter name and corresponding value to document
                        document[counterName] = counterValue
            except Exception as e:
                logger.warning("Unable to process {0} due to {1}: ".format(familyObj.fileName, e), __file__)
