from csv import reader
import sys
import re
from csv import reader
from datetime import datetime
import os
import importlib

# Local libraries
BaseOperator = importlib.import_module("shelf.collectorprocess.operators.BaseOperator").BaseOperator
FamilyObject = importlib.import_module("shelf.collectorprocess.operators.FamilyObject").FamilyObject
logger = importlib.import_module("shelf.collectorprocess.logger").logger

class Operator(BaseOperator):
    # Class Constructor
    def __init__(self, operationParams, baseObject={}):
        BaseOperator.__init__(self, operationParams, baseObject=baseObject)

    def process(self, familyObj=FamilyObject(), baseObject={}):
        logger.debug("Reading NUANCE ETF SQM PM V2T file' contents...", __file__)
        filePath = familyObj.getFiles()[0]

        familyObj.clearDocuments()

        # Get files name to find the unitID
        fileName = os.path.basename(filePath) #nome do ficheiro sem o caminho

        #Tirar data do nome do ficheiro
        fileNameRegex = re.search(r'^(?P<unitID>.*)\-(?P<startTime>\d{8}).*(\d{6}).*\.edr*', fileName)

        #tirar unitID do nome do ficheiro
        unitID = fileNameRegex.group('unitID').upper()

        familyObj.setUnitID(unitID)

        familyObj.fileName = fileName
	#definir parametros para saber qual o ficheiro que esta a ser usado

        try:
            # Open file for writing
            f = open(filePath, 'r')
        except IOError:
            logger.error("Could not open sample file \"{0}\" in read mode: ".format(fileName), __file__)
            return

        columnsNames = ['CALLTYPE','USERTYPE','CALLEDNUMBER','CALLINGNUMBER','REQUESTTID','CALLINGCIRCLE','CFWREASON','CALLSTARTTIME','CALLENDTIME','FILEDEPOSIT','CALLDURATION','ANSWERDURATION','RECORDINGDURATION','CALLEDCIRCLE','USERPROFILESTATUS','ERRORCODE','COMPLETEBY','BALANCE','V2TSTATUS','FALLBACK','FALLBACKCALLSTATUS','V2TCONVERSIONTIME','DISTYPE','EMDURATION','ELIGIBILTYSTATUS','USERINPUT','CLIR','CALLACTION','CALLACTIONREASON','MEORESERVED']

        for line in reader(f, delimiter=','):
            try:
                document = dict(zip(columnsNames, line))
                document['INTERVAL'] = 0
                try:
                    data_time = familyObj.parseEnvelopeDataTime(document["CALLSTARTTIME"])
                except ValueError as e:
                    logger.warning("Could not build mediationEnvelope due to {0}: ".format(e), __file__)
                    continue

                #envelope
                familyObj.addDocument({"dataTime": data_time, "granularitySec": document['INTERVAL'], "data": document})
                self.nextOp(familyObj=familyObj, baseObject=baseObject)
                familyObj.clearDocuments()

            except Exception as e:
                print("Unable to process {0} in unit {1} because wrong format => {2}".format(fileName, unitID, e), __file__)
                continue
