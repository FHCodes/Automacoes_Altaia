from csv import reader
import sys
import re
from csv import reader
import gzip
import io
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
        logger.debug("Reading ERICSSON ETF SQM PM VoIP file' contents...", __file__)

        filePath = familyObj.getFiles()[0]

        familyObj.clearDocuments()

        fileName = os.path.basename(filePath)

        unitID = 'VOIP_CDRS'
        familyObj.setUnitID(unitID)

        familyObj.fileName = fileName #definir parametros para saber qual o ficheiro que esta a ser usado

        try:
            if os.path.splitext(fileName)[1] == ".gz":
                f = io.BufferedReader(gzip.open(filePath))
            else:
                f = open(filePath, 'r')
        except IOError:
            logger.error("Could not open sample file \"{0}\" in read mode: ".format(fileName), __file__)
            return

        columnsNames = ['CDRTYPEVERSION','STARTDATETIME','TRAFFICTYPE','CALLINGNUMBER','DIALEDDIGITS','CALLEDNUMBER','CALLINGNUMBERTYPE','CALLEDNUMBERTYPE','SERVICETYPE','DURATION','CALLSTATUS','RELEASECAUSE','RECORDCOMPLETEIND','ICID','SYSTEMTIMEZONE','USERTIMEZONE','ACCESSTYPE','LOCATION','ORIGINATINGREALM','SERVICEPROVIDERID','GROUPID','GROUPNUMBER','TRUNKGROUP','TRUNKGROUPINFORMATION','USERSESIONID','ORIGINALCALLINGNUMBER','REDIRECTINGREASON','INVOCATIONTIME','SERVICEINVOKED','INVOCATIONRESULT','ROUTENAME','ISUPNCR','PSTNRELEASECAUSE','MEDIAINFORMATION','MEDIA','PORT','PROTO','NUMBEROFPORTS','FTM','GRANULARITYPERIOD']

        for line in reader(f, delimiter='|'):
            if line[0].startswith('PT_'):
                try:
                    document = dict(zip(columnsNames, line))
                    document['GRANULARITYPERIOD'] = 15
                    try:
                        data_time = datetime.strptime(document["STARTDATETIME"], "%d%m%Y%H%M%S")
                        data_time = datetime.strftime(data_time,"%Y-%m-%d %H:%M:%S")
                        data_time = familyObj.parseEnvelopeDataTime(data_time)
                        document['STARTDATETIME'] = data_time
                    except ValueError as e:
                        logger.warning("Could not build mediationEnvelope due to {0}: ".format(e), __file__)
                        continue

                    #envelope
                    familyObj.addDocument({"dataTime": data_time, "granularitySec": document['GRANULARITYPERIOD'], "data": document})
                    self.nextOp(familyObj=familyObj, baseObject=baseObject)
                    familyObj.clearDocuments()

                except Exception as e:
                    print("Unable to process {0} in unit {1} because wrong format => {2}".format(fileName, unitID, e), __file__)
                    continue
