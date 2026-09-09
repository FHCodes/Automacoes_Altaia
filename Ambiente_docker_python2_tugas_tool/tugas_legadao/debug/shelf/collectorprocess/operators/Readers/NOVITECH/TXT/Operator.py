__version__ = '1.0'

__doc__ = '''
    NOVITECH OSS VAS VMS Performance CSV Reader
'''

__authors__ = [
	"Version 1.0: paulo-a-gil <paulo-a-gil@alticelabs.com>"
]

import os
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
        logger.debug("Reading NOVITECH OSS VAS VMS Performance CSV file' contents...", __file__)
        filesToProcess = familyObj.getFiles()
        familyObj.clearDocuments()

        for filePath in filesToProcess:
            familyObj = FamilyObject()

            fileName = os.path.basename(filePath)
            familyObj.fileName = fileName

            # If file is empty, bota fora :)
            if os.path.getsize(filePath) == 0:
                logger.warning("File {0} is empty.".format(fileName), __file__)
                continue

            # Try opening the file
            try:
                f = open(filePath, 'r')
            except IOError:
                logger.error("Could not open file \"{0}\" in read mode.".format(fileName), __file__)

            # Set familyObj Unit ID
            familyObj.setUnitID("PERFVOICEMAIL")

            try:
                init_counter = None
                document = dict()

                for line in csv.reader(f, delimiter=";"):
                    # Get first counter and assign it as init counter
                    if init_counter == None:
                        init_counter = line[3]
                        document.update({line[3].upper(): line[4]})
                        continue

                    # Checks if the counter name is equal to the init counter
                    # If True, the document is ready to be processed
                    if init_counter == line[3]:
                        # Set document granularity field
                        document["INTERVAL"] = 15

                        # Parse envelope data time
                        try:
                            datatime = familyObj.parseEnvelopeDataTime(document["STARTTIME"])
                        except ValueError as e:
                            logger.warning("Could not build mediationEnvelope due to {0}: ".format(e), __file__)
                            continue

                        # Proceed with envelope
                        familyObj.addDocument({"dataTime": datatime, "granularitySec": int(document["INTERVAL"] * 60), "data": document})
                        self.nextOp(familyObj=familyObj, baseObject=baseObject)
                        familyObj.clearDocuments()

                        # Reset document and update it with current line, which belongs to a different measurement
                        document = dict()
                        document.update({line[3].upper(): line[4]})
                    else:
                        # Get ANF from measurement if it isn't already processed
                        if "ANF" not in document.keys():
                            document["ANF"] = line[0]

                        # Process STARTIME from measurement if it isn't already processed
                        if "STARTTIME" not in document.keys():
                            document["STARTTIME"] = str(datetime.strptime(" ".join(line[1:3]), "%Y%m%d %H:%M:%S"))

                        # Update document with the new counter name and corresponding value
                        document.update({line[3].upper(): line[4]})

            except Exception as e:
                logger.warning("Unable to process {0} due to {1}: ".format(familyObj.fileName, e), __file__)
