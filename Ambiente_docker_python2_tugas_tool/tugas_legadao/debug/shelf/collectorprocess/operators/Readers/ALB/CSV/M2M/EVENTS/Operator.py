import re
import os
import ast
import importlib
#import sys #apenas usado para testar localmente
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
        familyObj.fileName = fileName #para saber qual o ficheiro que esta a ser usado

        f = None
        try:
            # Open file for writing
            f = open(filePath, 'r')
        except IOError:
            logger.error(
                "Could not open sample file \"{0}\" in read mode: ".format(fileName), __file__)

        for line in f.readlines():
            familyObj.clearDocuments()
            try:
                line = line.strip()
                line = line.split(';', 2)
                document = dict()
                document['READ_DATE'] = line[0]
                valid = line[1]
                document.update(ast.literal_eval(line[2]))
                document['DATETIME'] = document["CALL_ATT_TIME"].split(" ")[0] + " " + document["CALL_ATT_TIME"].split(" ")[1]
                try:
                    data_time = familyObj.parseEnvelopeDataTime(document["DATETIME"])
                except ValueError as e:
                    logger.warning("Could not build mediationEnvelope due to {0}: ".format(e), __file__)
                    continue

                #logger.warning(valid)
                # envelope
                if valid == 'VALID':
                    familyObj.setUnitID('M2M_CDR_CARE_EVENTBROKER')
                elif valid == 'INVALID':
                    familyObj.setUnitID('M2M_CDR_CARE_INVALIDEVENTS')

                familyObj.addDocument({"dataTime": data_time, "granularitySec": 1440, "data": document})
                self.nextOp(familyObj=familyObj, baseObject=baseObject)
                familyObj.clearDocuments()

            except Exception as e:
                print("Unable to process {0} because wrong format => {1}".format(fileName, e), __file__)
                continue
