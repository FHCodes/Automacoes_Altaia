__version__ = '1.0'

__doc__ = '''
    HUAWEI OSS VAS SMS-C Performance CSV Reader
'''

__authors__ = [
	"Version 1.1: paulo-a-gil <paulo-a-gil@alticelabs.com>"
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

        self._unitMapping = json.load(open('/opt/alticelabs/namf/src/shelf/collectorprocess/operators/Readers/HUAWEI/CSV/VAS/SMSC/unitMapping.json'))
        self._neMapping = json.load(open('/opt/alticelabs/namf/src/shelf/collectorprocess/operators/Readers/HUAWEI/CSV/VAS/SMSC/neMapping.json'))
        self._ip_omc = baseObject.args.sourceId

    def process(self, familyObj=FamilyObject(), baseObject={}):
        logger.debug("Reading HUAWEI OSS VAS SMS-C Performance CSV file' contents...", __file__)
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

            # Get OMC IP and UnitID from fileName
            regex = re.match("^(?P<UnitID>.+?)_Report[-|_]((MOMT|SRI)|Minutely).*$", fileName)
            unitID = regex.group("UnitID").upper() + "_" + regex.group(2).upper()
            unitID = unitID.replace("_MINUTELY","")

            # Set familyObj Unit ID
            familyObj.setUnitID(unitID)

            # Get corresponding header from unitMapping
            header = self._unitMapping[unitID]
            header = [item.replace(" ", "_").upper() for item in header]

            # Get corresponding SMSC NE name
            smsc_name = self._neMapping[self._ip_omc]

            try:
                nLine = 0
                for line in csv.reader(f):
                    nLine += 1
                    # If line is empty, skip line
                    if not line:
                        continue

                    # Checks if the length of the header equals the length of the line
                    if len(header) != len(line):
                        logger.warning("Number of values in line {0} is different than number of announced columns in sample \"{1}\"".format(nLine, fileName))
                        continue

                    # Remove unwanted spaces
                    line = [item.replace(" ", "") for item in line]
		    line[0] = line[0].decode("utf-8-sig").encode("utf-8")

                    # Creates a dict based on a zip between the header and parsed line items
                    document = dict(zip(header, line))

                    # Format BEGINTIME
                    document["BEGINTIME"] = datetime.strftime(datetime.strptime(document["BEGINTIME"], "%Y-%m-%d%H:%M"), "%Y-%m-%d %H:%M:%S")
                    # Set SMSC name based on OMC IP
                    document["SMSC"] = smsc_name
                    # Set document Granularity Field
                    document["INTERVAL"] = 5

                    # Parse envelope data time
                    try:
                        datatime = familyObj.parseEnvelopeDataTime(document["BEGINTIME"])
                    except ValueError as e:
                        logger.warning("Could not build mediationEnvelope due to {0}: ".format(e), __file__)
                        continue

                    # Proceed with envelope
                    familyObj.addDocument({"dataTime": datatime, "granularitySec": int(document['INTERVAL'] * 60), "data": document})
                    self.nextOp(familyObj=familyObj, baseObject=baseObject)
                    familyObj.clearDocuments()

            except Exception as e:
                logger.warning("Unable to process {0} due to {1}: ".format(familyObj.fileName, e), __file__)
