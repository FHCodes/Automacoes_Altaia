import re
import os
import importlib
#import sys #apenas usado para testar localmente
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
        logger.debug("Reading Altice Labs Plat M2M CSV file' contents...", __file__)
        filePath = familyObj.getFiles()[0]

        familyObj.clearDocuments()

        # Get files name to find the unitID
        fileName = os.path.basename(filePath) #nome do ficheiro sem o caminho

        #Tirar data do nome do ficheiro
        fileNameRegex = re.search(r'^(?P<unitID>.*?)\_(?P<startTime>\d+)\.csv.*', fileName) #fazer match com M2M_ClientDetail_20201122030001.csv
        startTime = datetime.strptime(fileNameRegex.group('startTime'), "%Y%m%d%H%M%S")
        startTime = datetime.strftime(startTime,"%Y-%m-%d %H:%M:%S")

        #tirar unitID do nome do ficheiro
        unitID = fileNameRegex.group('unitID').upper()

        familyObj.setUnitID(unitID)

        familyObj.fileName = fileName #para saber qual o ficheiro que esta a ser usado

        f = None
        try:
            # Open file for writing
            f = open(filePath, 'r')
        except IOError:
            logger.error(
                "Could not open sample file \"{0}\" in read mode: ".format(fileName), __file__)

        columnsNames = list()

        for line in reader(f, delimiter=';'):
            if not line:
                continue

            line = [item.decode("latin-1") for item in line]

            if columnsNames == list():
                columnsNames = line
                continue

            if len(line) != len(columnsNames):
                continue

            try:
                document = dict(zip(columnsNames, line))
                document['DATETIME'] = startTime

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
                print("Unable to process {0} in unit {1} because wrong format => {2}".format(fileName, unitID, e), __file__)
                continue
