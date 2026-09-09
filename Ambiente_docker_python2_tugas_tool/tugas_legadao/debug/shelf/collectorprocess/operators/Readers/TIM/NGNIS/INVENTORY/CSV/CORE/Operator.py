import re
import os
import importlib
from csv import reader
from datetime import datetime

# Local libraries
BaseOperator = importlib.import_module("shelf.collectorprocess.operators.BaseOperator").BaseOperator
FamilyObject = importlib.import_module("shelf.collectorprocess.operators.FamilyObject").FamilyObject
logger = importlib.import_module("shelf.collectorprocess.logger").logger

class Operator(BaseOperator):
    # Class Constructor
    def __init__(self, operationParams, baseObject={}):
        BaseOperator.__init__(self, operationParams, baseObject=baseObject)

    def process(self, familyObj=FamilyObject(), baseObject={}):
        logger.debug("Reading NGNIS CORE Inventory CSV file' contents...", __file__)
        filePath = familyObj.getFiles()[0]

        familyObj.clearDocuments()

        # Get files name to find the unitID
        fileName = os.path.basename(filePath) #nome do ficheiro sem o caminho

        #Tirar data do nome do ficheiro
        fileNameRegex = re.search(r'^.*?_(?P<startTime>\d{8}_\d{6}).*\.csv$', fileName)
        startTime = datetime.strptime(fileNameRegex.group('startTime'), "%Y%m%d_%H%M%S")
        startTime = datetime.strftime(startTime,"%Y-%m-%d %H:%M:%S")

        familyObj.setUnitID('NGNIS_SSW_ROUTES')

        familyObj.fileName = fileName

        try:
            # Open file for writing
            f = open(filePath, 'r')
        except IOError:
            logger.error(
                "Could not open sample file \"{0}\" in read mode: ".format(fileName), __file__)

        columnsNames = ["ROUTEVOICE_NAME","ROUTE_VOICE_STATUS","TRAIL","SUBSCRIBER_NAME","FULLNAME","RELATIVENAME"]
        firstLine = True

        for line in reader(f, delimiter=';'):
            if firstLine == True:
                firstLine = False
                continue

            try:
                line = [item.decode("latin-1") for item in line]
                document = dict(zip(columnsNames, line))
                document['DATETIME'] = startTime
                document['INTERVAL'] = 1440

                try:
                    data_time = familyObj.parseEnvelopeDataTime(document["DATETIME"])
                except ValueError as e:
                    logger.warning("Could not build mediationEnvelope due to {0}: ".format(e), __file__)
                    continue
                # envelope
                familyObj.addDocument({"dataTime": data_time, "granularitySec": 1440, "data": document})
                self.nextOp(familyObj=familyObj, baseObject=baseObject)
                familyObj.clearDocuments()

            except Exception as e:
                logger.warning("Unable to process {0} in unit {1} because wrong format => {2}".format(fileName, 'NGNIS_SSW_ROUTES', e), __file__)
                continue
