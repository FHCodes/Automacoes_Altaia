__version__ = '1.0'

__doc__ = '''
    Mahindra TSLEE Plat Performance IN CSV Reader
'''

__authors__ = [
	"Version 1.1: paulo-a-gil <paulo-a-gil@alticelabs.com>"
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
        logger.debug("Mahindra TSLEE Plat Performance IN file contents...", __file__)
        filesToProceess = familyObj.getFiles()
        familyObj.clearDocuments()

        for filePath in filesToProceess:
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

            # Get Unit ID from file name
            fileNameRegex = re.search(r'^(?P<unitID>.+?_.+?)_.+?\.csv$', fileName)
            unitID = fileNameRegex.group('unitID')
            familyObj.setUnitID(unitID)

            # Sort CSV file in order to group counters
            sorted_csv = sorted(csv.reader(f), key=lambda row: (row[0], row[1]))

            # Remove header from sorted csv since it is not necessary
            header = ['SITE', 'SERVER', 'DATA_DESDE', 'DATA_ATE', 'VARIAVEL', 'VALOR']
            sorted_csv.remove(header)

            try:
                # Empty dict to store counter names and values
                document = dict()
                # Flag to indicate if we already have a PK associated with the counters being parsed
                pk = False

                for line in sorted_csv:
                    # Gets PK fields if document PK is not yet defined
                    if not pk:
                        document["SITE"] = line[0]
                        document["SERVER"] = line[1]
                        document["STARTTIME"] = line[2]
                        document["ENDTIME"] = line[3]
                        document["GRANULARITYPERIOD"] = 15

                        # Set PK to True since we have a PK for the current counter
                        pk = True

                        # Update document with current parsed counter
                        document.update({line[4].replace(" ","_").upper(): line[5]})

                    # Current measurement PK is different from document PK
                    # TL;DR -> It means that current line belongs to another measurement and document can be processed
                    elif document["SITE"] != line[0] or document["SERVER"] != line[1] or document["STARTTIME"] != line[2]:
                        document["STARTTIME"] = datetime.strftime(datetime.strptime(document["STARTTIME"], "%Y%m%d_%H%M%S"), "%Y-%m-%d %H:%M:%S")
                        document["ENDTIME"] = datetime.strftime(datetime.strptime(document["ENDTIME"], "%Y%m%d_%H%M%S"), "%Y-%m-%d %H:%M:%S")

                        # Parse envelope DataTime
                        try:
                            timestamp = familyObj.parseEnvelopeDataTime(document["STARTTIME"])
                        except ValueError as e:
                            logger.warning("Could not build mediationEnvelope due to {0}: ".format(e), __file__)
                            continue

                        # Setting up the envelope
                        familyObj.addDocument({"dataTime": timestamp, "granularitySec": int(document["GRANULARITYPERIOD"]*60), "data": document})
                        self.nextOp(familyObj=familyObj, baseObject=baseObject)
                        familyObj.clearDocuments()

                        # Create an empty document to process another measurement
                        document = dict()
                        # Set PK to False since we're parsing a new measurement
                        pk = False
                        # Update document with current parsed counter
                        document.update({line[4].replace(" ","_").upper(): line[5]})

                    # Continue processing counters and update document with
                    else:
                        document.update({line[4].replace(" ","_").upper(): line[5]})
            except Exception as e:
                logger.warning("Unable to process {0} due to {1}: ".format(familyObj.fileName, e), __file__)