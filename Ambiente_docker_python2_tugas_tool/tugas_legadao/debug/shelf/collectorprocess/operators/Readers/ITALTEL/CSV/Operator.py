__version__ = '1.0'

__doc__ = '''
    ITALTEL IMS IMCS Performance CSV Reader
'''

__authors__ = [
	"Version 1.0: paulo-a-gil <paulo-a-gil@alticelabs.com>"
]

import os
import re
from csv import reader
from datetime import datetime, timedelta
import importlib

# Local libraries
BaseOperator = importlib.import_module("shelf.collectorprocess.operators.BaseOperator").BaseOperator
FamilyObject = importlib.import_module("shelf.collectorprocess.operators.FamilyObject").FamilyObject
logger = importlib.import_module("shelf.collectorprocess.logger").logger

class Operator(BaseOperator):

    # Class constructor
    def __init__(self, operationParams, baseObject={}):
        BaseOperator.__init__(self, operationParams, baseObject=baseObject)

    def process(self, familyObj=FamilyObject(), baseObject={}):
        logger.debug("Reading ITALTEL IMS IMCS Performance CSV file' contents...", __file__)
        filePath = familyObj.getFiles()[0]

        familyObj.clearDocuments()

        fileName = os.path.basename(filePath)
        familyObj.fileName = fileName

        # If file is empty, bota fora :)
        if os.path.getsize(filePath) == 0:
            logger.warning("File {0} is empty.".format(fileName), __file__)
            return

        # Try opening the file
        try:
            f = open(filePath, 'r')
        except IOError:
            logger.error("Could not open file \"{0}\" in read mode.".format(fileName), __file__)

        header = []
        # Exclude list: list of strange counters coming from the sample files
        exclude_list = ['TIME','(MEAN)']

        nLine = 0
        try:
            for line in reader(f):
                nLine += 1
                # If line is empty, skip
                if not line:
                    continue

                # Checks if line is an header line and thus removing blank counters
                if line[0] == 'jobId':
                    header = [field.upper() for field in line if field != '' and field not in exclude_list]
                    header[1] = 'ENDTIME'
                    continue

                # Remove blank spaces from line values
                line = [value for value in line if value != '']

                # Checks if the length of the header equals the length of the line
                if len(header) != len(line):
                    logger.warning("Number of values in line {0} is different than number of announced columns in sample \"{1}\"".format(nLine, fileName))
                    continue

                # Creates a zip between the header and line items
                document = dict(zip(header, line))

                document['ENDTIME'] = datetime.strptime(document['ENDTIME'][:-6], "%Y-%m-%dT%H:%M:%S.%f")
                document['BEGINTIME'] = datetime.strftime(document['ENDTIME'] - timedelta(minutes=15), "%Y-%m-%d %H:%M:%S")
                document['ENDTIME'] = datetime.strftime(document['ENDTIME'], "%Y-%m-%d %H:%M:%S")
                document['DURATION'] = 15
                document['MEASUREMENTDATAOBJECT'] = fileName.replace('.csv','')

                familyObj.setUnitID(re.sub("\\S+__\\S+-", '', document['JOBID']).upper())
                familyObj.clearDocuments()

                try:
                    begintime = familyObj.parseEnvelopeDataTime(document["BEGINTIME"])
                except ValueError as e:
                    logger.warning("Could not build mediationEnvelope due to {0}: ".format(e), __file__)
                    continue

                familyObj.addDocument({"dataTime": begintime, "granularitySec": int(document['DURATION'] * 60), "data": document})
                self.nextOp(familyObj=familyObj, baseObject=baseObject)
                familyObj.clearDocuments()

        except Exception as e:
            logger.warning("Unable to process {0} due to {1}: ".format(familyObj.fileName, e), __file__)
