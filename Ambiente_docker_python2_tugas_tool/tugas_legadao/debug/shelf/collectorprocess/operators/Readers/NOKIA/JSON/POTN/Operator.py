__version__ = '1.0'

__doc__ = '''
    NOKIA NFMT TRANS PoTN Inventory JSON Reader
'''

__authors__ = [
	"Version 1.0: paulo-a-gil <paulo-a-gil@alticelabs.com>"
]

import os
import re
import ijson
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
                f = ijson.parse(open(filePath, "r"))
            except IOError:
                logger.error("Could not open file \"{0}\" in read mode.".format(fileName), __file__)

            # Get datetime from filename
            fileNameRegex = re.match("^GetAllEQPTResponse_(?P<DATETIME>\d+).json$", fileName)
            fileNameDatetime = fileNameRegex.group("DATETIME")
            fileNameDatetime = datetime.strftime(datetime.strptime(fileNameRegex.group("DATETIME"), "%Y%m%d%H%M"), "%Y-%m-%d %H:%M:%S")

            # Set unit ID
            familyObj.setUnitID("DISC_POTN_INVENTORY_INFO")

            # Init variables
            document = dict()
            key = None

            # Parse envelope data time
            try:
                datatime = familyObj.parseEnvelopeDataTime(fileNameDatetime)
            except ValueError as e:
                logger.warning("Could not build mediationEnvelope due to {0}: ".format(e), __file__)
                continue

            try:
                for prefix, event, value in f:

                    # start_map events mark the beginning of the document,
                    # except inside the attributeNameValue nest
                    if event == "start_map":
                        if prefix.split(".")[-1] != "attributeNameValue":
                            document = dict()

                    # end_map events mark the end of the document
                    # except inside the attributeNameValue nest
                    elif event == "end_map":
                        if prefix.split(".")[-1] != "attributeNameValue":

                            # Set DATETIME and GRANULARITY
                            document["DATETIME"] = fileNameDatetime
                            document["GRANULARITY"] = 60*24

                            # Proceed with envelope
                            familyObj.addDocument({"dataTime": datatime, "granularitySec": int(document["GRANULARITY"] * 60), "data": document})
                            self.nextOp(familyObj=familyObj, baseObject=baseObject)
                            familyObj.clearDocuments()

                    # map_key events represent the parameter name,
                    # ignoring attributeNameValue
                    elif event == "map_key":
                        if value != "attributeNameValue":
                            key = value.upper()

                    # string events represent the value of the key
                    elif event == "string":
                        val = value.strip()
                        document.update({key:val})
                        key = None

            except Exception as e:
                logger.warning("Unable to process {0} due to {1}: ".format(familyObj.fileName, e), __file__)
