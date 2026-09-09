__version__ = '1.0'

__doc__ = '''
    HUAWEI U2020 Transport PTN Inventory Reader
'''

__authors__ = [
	"Version 1.0: paulo-a-gil <paulo-a-gil@alticelabs.com>"
]


import os
import re
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
        logger.debug("Reading NOKIA SDC GPON Inventory CSV file' contents...", __file__)
        filesToProcess = familyObj.getFiles()
        familyObj.clearDocuments()

        for filePath in filesToProcess:
            # If file is empty, bota fora :)
            if os.path.getsize(filePath) == 0:
                logger.warning("File {0} is empty.".format(os.path.basename(filePath)), __file__)
                continue

            # Get file's name to find the unitID
            fileName = os.path.basename(filePath)
            familyObj.fileName = fileName

            fileNameRegex = re.search(r"^(?P<unitID>.+)_(?P<datetime>\d+).per$", fileName)
            unitID = fileNameRegex.group("unitID").upper()
            dt = fileNameRegex.group("datetime")

            # Set Unit ID
            familyObj.setUnitID(unitID)

            # Open the file in reading mode
            try:
                f = open(filePath, 'r')
            except IOError:
                logger.error("Could not open sample file \"{0}\" in read mode: ".format(fileName), __file__)

            document = dict()

            try:
                for line in f:
                    # Strip line
                    line = line.strip()

                    # If line is empty, skip it
                    if not line:
                        continue

                    # Clear document
                    if re.compile("^\[.+\]$").match(line):
                        if document != dict():
                            document["GRANULARITY"] = 1440
                            document["DATETIME"] = datetime.strftime(datetime.strptime(dt, "%Y%m%d"), "%Y-%m-%d %H:%M:%S")
                            document["PROCESSDATE"] = datetime.strftime(datetime.strptime(document["PROCESSDATE"][:-3], "%Y%m%d%H%M%S"), "%Y-%m-%d %H:%M:%S")

                            try:
                                data_time = familyObj.parseEnvelopeDataTime(document["DATETIME"])
                            except ValueError as e:
                                logger.warning("Could not build mediationEnvelope due to {0}: ".format(e), __file__)
                                continue

                            familyObj.addDocument({"dataTime": data_time, "granularitySec": int(document["GRANULARITY"]*60), "data": document})
                            self.nextOp(familyObj=familyObj, baseObject=baseObject)
                            familyObj.clearDocuments()
                            document = dict()
                        else:
                            document = dict()
                        continue

                    # Extract name and value from line
                    fields = line.split("=", 1)

                    # Add extracted fields to document
                    document[fields[0].upper()] = fields[1]

            except Exception as e:
                logger.warning("Unable to process file {0} because => {1}".format(familyObj.fileName, e), __file__)
                continue
