__version__ = '1.0'

__doc__ = '''
    NOKIA SDC GPON Inventory Reader
'''

__authors__ = [
    "Version 1.0: paulo-a-gil <paulo-a-gil@alticelabs.com>"
]

import os
import io
import re
import csv
import tarfile
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

        self.timestamp_regex = re.compile("^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}).*$")

    def process(self, familyObj=FamilyObject(), baseObject={}):
        logger.debug("Reading NOKIA SDC GPON Inventory CSV file' contents...", __file__)
        filesToProcess = familyObj.getFiles()
        familyObj.clearDocuments()

        for filePath in filesToProcess:
            # If file is empty, bota fora :)
            if os.path.getsize(filePath) == 0:
                logger.warning("File {0} is empty.".format(os.path.basename(filePath)), __file__)
                continue

            # Open tar file
            tar = tarfile.open(filePath)

            # Loop through csv files in tar
            for member in tar.getmembers():
                familyObj.clearDocuments()

                fileName = member.name
                familyObj.fileName = fileName

                familyObj.unitID = re.sub(r"(?P<unitID>iSAM_\w+|IHUB_\w+).csv.*", r"\1", fileName).upper()

                # Extract member
                try:
                    f = tar.extractfile(member)
                except:
                    logger.warning(
                        "Could not extract file {0} from tar file {1}.".format(member.name, os.path.basename(filePath)),
                        __file__)
                    continue

                # Check if member is not a regular file or link
                if f is not None:
                    # Convert bytes into a CSV-like object
                    try:
                        csv_file = io.StringIO(tar.extractfile(member).read().decode('utf-8'))
                    except:
                        logger.warning(
                            "Could not decode file {0} to utf-8.".format(member.name, os.path.basename(filePath)),
                            __file__)
                        continue

                    # Try read CSV file
                    try:
                        object_type = None
                        header = list()
                        baseDocument = dict()

                        for line in csv.reader(csv_file):

                            # Parse first line into DATETIME field
                            if "DATETIME" not in baseDocument:
                                timestamp_match = self.timestamp_regex.match(line[1])

                                if timestamp_match is not None:
                                    baseDocument["DATETIME"] = datetime.strftime(
                                        datetime.strptime(timestamp_match.group(1), "%Y-%m-%dT%H:%M:%S"),
                                        "%Y-%m-%d %H:%M:%S")
                                    continue
                            # Parse second line as unit ID
                            if not object_type:
                                object_type = line[1]
                                continue
                            # Parse third line into "NE NAME"
                            if "NE NAME" not in baseDocument:
                                baseDocument["NE NAME"] = line[1]
                                continue
                            # Parse fourth line into "NE TYPE"
                            if "NE TYPE" not in baseDocument:
                                baseDocument["NE TYPE"] = line[1]
                                continue
                            else:
                                # Skip empty lines
                                if not line:
                                    continue

                                # Parse header line
                                if line[0] == "Object ID" and header == list():
                                    header = line
                                    header = [item.upper() for item in header]
                                    continue

                                if len(header) != len(line):
                                    logger.warning(
                                        "Number of values in current line is different than number of announced columns in sample".format(
                                            fileName))
                                    continue

                                # Create a document from de zip between header and current line
                                document = dict(zip(header, line))

                                # Append baseDocument info to the document
                                document.update(baseDocument)

                                # Add granularity field
                                document["GRANULARITYPERIOD"] = 15

                                # Parse envelope data time
                                try:
                                    datatime = familyObj.parseEnvelopeDataTime(document["DATETIME"])
                                except ValueError as e:
                                    logger.warning("Could not build mediationEnvelope due to {0}: ".format(e), __file__)
                                    continue

                                # Proceed with envelope
                                familyObj.addDocument(
                                    {"dataTime": datatime, "granularitySec": int(document["GRANULARITYPERIOD"] * 60),
                                     "data": document})
                                self.nextOp(familyObj=familyObj, baseObject=baseObject)
                                familyObj.clearDocuments()

                    except Exception as e:
                        logger.warning("Unable to process {0} due to {1}: ".format(familyObj.fileName, e), __file__)
