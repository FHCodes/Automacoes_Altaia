__version__ = '1.0'

__doc__ = '''
    ERICSSON OSS RAN ROAMING 2G  Reader
'''

__authors__ = [
    "Version 1.0: marco-a-jeronimo <marco-a-jeronimo@alticelabs.com>"
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

        # Define the regular expressions
        self.pattern_lai = re.compile(r'^((\d+)-(\d+)-(\d+))$')
        self.pattern_nrrg = re.compile(r'^((\d+)-(\d+)-(\d+))\s*([\d\s]*)$')

    def process(self, familyObj=FamilyObject(), baseObject={}):
        logger.debug("Reading ERICSSON OSS RAN ROAMING 2G txt file' contents...", __file__)
        filesToProcess = familyObj.getFiles()
        familyObj.clearDocuments()

        for filePath in filesToProcess:
            familyObj = FamilyObject()

            # If file is empty
            if os.path.getsize(filePath) == 0:
                logger.warning("File {0} is empty.".format(os.path.basename(filePath)), __file__)
                continue

            fileName = os.path.basename(filePath)
            familyObj.fileName = fileName

            fileNameRegex = re.search(r"^(?P<MSC>.+)_(?P<datetime>\d+).txt$", fileName)
            unitID = "RADIO_ROAMING_2G_LAC"
            dt = fileNameRegex.group("datetime")
            # Extracting MSC from the file name
            msc = fileNameRegex.group("MSC")

            # Set Unit ID
            familyObj.setUnitID(unitID)

            # Try opening the file
            try:
                fFile = open(filePath, 'r')

                document = dict()
                try:
                    for line in fFile:
                        line = line.strip()

                        # If line is empty, skip it
                        if not line:
                            continue

                        match_lai = self.pattern_lai.match(line)
                        match_nrrg = self.pattern_nrrg.match(line)

                        document["GRANULARITYPERIOD"] = 86400
                        document["DATETIME"] = datetime.strftime(datetime.strptime(dt, "%Y%m%d"), "%Y-%m-%d %H:%M:%S")
                        try:
                            data_time = familyObj.parseEnvelopeDataTime(document["DATETIME"])
                            granularity_sec = familyObj.parseEnvelopeGranularitySec(int(document["GRANULARITYPERIOD"]))
                        except ValueError as e:
                            logger.warning("Could not build mediationEnvelope due to {0}: ".format(e), __file__)
                            continue

                        if match_lai:
                            lai = match_lai.group(1)
                            document["MSC"] = msc
                            document["LAI"] = lai
                            document["MCC"] = match_lai.group(2)
                            document["MNC"] = match_lai.group(3)
                            document["LAC"] = match_lai.group(4)
                            document["NGGR"] = None
                            familyObj.addDocument(
                                {"dataTime": data_time, "granularitySec": granularity_sec, "data": document})
                            self.nextOp(familyObj=familyObj, baseObject=baseObject)
                        elif match_nrrg:
                            lai = match_nrrg.group(1)
                            nggr = match_nrrg.group(5).strip() if match_nrrg.group(5) else None
                            document["MSC"] = msc
                            document["LAI"] = lai
                            document["MCC"] = match_nrrg.group(2)
                            document["MNC"] = match_nrrg.group(3)
                            document["LAC"] = match_nrrg.group(4)
                            document["NGGR"] = nggr
                            familyObj.addDocument(
                                {"dataTime": data_time, "granularitySec": granularity_sec, "data": document})
                            self.nextOp(familyObj=familyObj, baseObject=baseObject)

                        familyObj.clearDocuments()
                        document = dict()

                except Exception as e:
                    logger.warning("Unable to process file {0} because => {1}".format(familyObj.fileName, e), __file__)
                    continue

            except IOError:
                logger.error("Could not open file \"{0}\" in read mode.".format(fileName), __file__)
