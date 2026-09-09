__version__ = '1.0'

__doc__ = '''
    NOKIA NFM-T TRANS PoTN Performance CSV Reader
'''

__authors__ = [
	"Version 1.0: paulo-a-gil <paulo-a-gil@alticelabs.com>"
]

import os
import csv
import json
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

        self._unitMapping = json.load(open('/opt/alticelabs/namf/src/shelf/collectorprocess/operators/Readers/NOKIA/CSV/POTN/unitMapping.json'))

    def process(self, familyObj=FamilyObject(), baseObject={}):
        logger.debug("Reading NOKIA NFMT TRANS POTN Performance CSV file' contents...", __file__)
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

            try:
                baseDocument = dict()
                header = list()

                for line in csv.reader(f):
                    # Skip empty lines
                    if not line:
                        continue

                    # If header is empty, get fisrt line as header
                    if not header:
                        header = line
                        header = [item.upper() for item in header]
                        continue

                    # Check if length of header equals to the length of the current line
                    if len(header) != len(line):
                        logger.warning("Number of values in current line is different than number of announced columns in sample".format(fileName))
                        continue

                    # Create e dict from the zip between the header and current line
                    baseDocument = dict(zip(header,line))

                    # Reset document dict
                    document = dict()

                    # Get ID fields from baseDocument
                    document["MEASURE"] = baseDocument.pop("CONNECTION NAME")
                    document["TRANSPORT"] = document["MEASURE"]
                    document["POTN"] = baseDocument.pop("NE")
                    document["TPOBJECT"] = baseDocument["TP"]
                    document["TP"] = baseDocument["TP"]
                    document["PORTENTITY"] = document["TPOBJECT"]
                    document["SIDE"] = baseDocument.pop("LOCATION").replace(" ","")
                    document["RATE"] = baseDocument.pop("LAYER RATE")
                    document["DIRECTION"] = baseDocument["DIRECTION"]

                    # Set UnitID based on TP object and DIRECTION
                    if "Queue" in document["TP"]:
                        if "TRMT" in baseDocument["DIRECTION"]:
                            unitID = "PSS_QUEUE_OUTGOING"
                        else:
                            unitID = "PSS_QUEUE_INCOMING"
                    else:
                        if "TRMT" in baseDocument["DIRECTION"]:
                            unitID = "PSS_INTERFACE_OUTGOING"
                        else:
                            unitID = "PSS_INTERFACE_INCOMING"

                    # If unitID is not defined, skip line
                    if not unitID:
                        continue

                    # Set unit ID on family Object
                    familyObj.setUnitID(unitID)

                    # Format DATETIME
                    document["DATETIME"] = baseDocument.pop("TIME")
                    document["DATETIME"] = datetime.strptime(document["DATETIME"], "%m/%d/%Y %H:%M")
                    document["DATETIME"] = datetime.strftime(document["DATETIME"], "%Y-%m-%d %H:%M:%S")

                    # Set GRANULARTITY
                    document["GRANULARITY"] = 15

                    # Filter counters based on unit mapping
                    for counter in baseDocument:
                        if counter not in ["DATETIME", "MEASURE", "POTN", "TPOBJECT", "TP", "PORTENTITY", "SIDE", "GRANULARITY", "TRANSPORT", "RATE", "DIRECTION"]:
                            if counter in self._unitMapping[unitID]:
                                document[counter] = baseDocument[counter]

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

            except Exception as e:
                logger.warning("Unable to process {0} due to {1}: ".format(familyObj.fileName, e), __file__)