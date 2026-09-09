__version__ = '1.0'

__doc__ = '''
    AlticeLabs FTTH AAA Performance CSV Reader
'''

__authors__ = [
	"Version 1.0: paulo-a-gil <paulo-a-gil@alticelabs.com>"
]

import os
import re
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
        logger.debug("Reading AlticeLabs FTTH AAA Performance CSV file' contents...", __file__)
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
            try:
                f = open(filePath, "r")
            except IOError:
                logger.error("Could not open file \"{0}\" in read mode.".format(fileName), __file__)


            # Extract Unit ID from filename
            filenameRegex = re.compile(r"^(?P<HOSTNAME>[a-zA-Z0-9]+-?\d+)-(?P<UNIT>\S+)-\d+.csv").match(fileName)

            unitID = None
            if filenameRegex:
                unitID = filenameRegex.group("UNIT")
            else:
                logger.error("File \"{0}\" not expected.".format(fileName), __file__)
                continue

            # Set Unit ID
            familyObj.setUnitID(unitID)

            # Init empty header
            header = list()

            try:
                for line in csv.reader(f):
                    # Skip empty lines
                    if not line:
                        continue
                    # If header is empty, process header
                    if not header:
                        header = line
                        header = [item.upper() for item in header]
                        continue

                    # Create a document from the zip between the header and current line
                    document = dict(zip(header,line))

                    # Format GRANULARITYPERIOD
                    document["GRANULARITYPERIOD"] = int(document["GRANULARITYPERIOD"]) / 60

                    # Parse envelope data time
                    try:
                        datatime = familyObj.parseEnvelopeDataTime(document["STARTTIME"])
                    except ValueError as e:
                        logger.warning("Could not build mediationEnvelope due to {0}: ".format(e), __file__)
                        continue

                    # Proceed with envelope
                    familyObj.addDocument({"dataTime": datatime, "granularitySec": int(document["GRANULARITYPERIOD"]) * 60, "data": document})
                    self.nextOp(familyObj=familyObj, baseObject=baseObject)
                    familyObj.clearDocuments()

            except Exception as e:
                logger.warning("Unable to process {0} due to {1}: ".format(familyObj.fileName, e), __file__)
                continue
