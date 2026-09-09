#!/usr/bin/env python
__version__ = '1.0'

__doc__ = '''
            SNMP to Mongo Reader
          '''

__authors__ = [
    "Version 1.0: Bruno Silva <bruno-e-silva@alticelabs.com>"
]

import os, json
import re
from datetime import datetime
import importlib
from csv import reader

# Local libraries
BaseOperator = importlib.import_module("shelf.collectorprocess.operators.BaseOperator").BaseOperator
FamilyObject = importlib.import_module("shelf.collectorprocess.operators.FamilyObject").FamilyObject
logger = importlib.import_module("shelf.collectorprocess.logger").logger
mongoCon = importlib.import_module(
    "shelf.collectorprocess.operators.OutputManagers.Mongo.Operator").mongoConnection


class Operator(BaseOperator):

    # Class constructor
    def __init__(self, operationParams, baseObject={}):
        BaseOperator.__init__(self, operationParams, baseObject=baseObject)
        # self._mongoConnection = mongoCon(json.load(open('/opt/alticelabs/namf/src/shelf/collectorprocess/config/mongo_config.json')))

        self.snmp_config = json.load(open('/opt/alticelabs/namf/src/shelf/collectorprocess/config/snmp_mongo_config.json'))

        self._mongoConnection = mongoCon(
            {"username": self.snmp_config["username"], "password": self.snmp_config["password"], "dbName": self.snmp_config["db"], "collectionName": self.snmp_config["instances_collection"],
             "connectionString": self.snmp_config["connection_string"]})

        self.version_translation = {
            "V2C": "v2c",
            "V1": "v1",
            "V3": "v3",
            "1": "v1",
            "2C": "v2c",
            "2": "v2c",
            "3": "v3"
        }

    def process(self, familyObj=FamilyObject(), baseObject={}):
        mongoCollection = self._mongoConnection.getConnection()
        logger.debug("Reading TDT file' contents...", __file__)
        filePath = familyObj.getFiles()[0]
        familyObj.fileName = os.path.basename(filePath)
        unitId = (re.match(r'^.*_(?P<unitId>[^_]*)_\d*.csv', familyObj.fileName)).group('unitId').upper()

        if unitId == 'SONDA':
            self.processSonda(filePath, familyObj.fileName)
        else:
            self.processExcitador(filePath, familyObj.fileName)

    def processSonda(self, filePath, fileName):
        data = datetime.today()
        data = datetime.strptime('{0}-{1}-{2} 00:00:00'.format(data.year, data.month, data.day), '%Y-%m-%d %H:%M:%S')
        try:
            header = list()
            lineNum = 0
            f = open(filePath, 'r')
            for line in reader(f, delimiter=';'):
                lineNum += 1
                if lineNum == 1:
                    # vendorIdDate = datetime.strptime(line[0].strip(), '%Y-%m-%d %H:%M:%S')
                    continue
                elif lineNum == 2:
                    continue
                elif lineNum == 3:
                    header = line
                    continue

                document = dict(zip(header, line))

                # vendor e model
                newDocument = dict()
                newDocument['requestParameters'] = dict()
                newDocument['requestParameters']['bulkSize'] = '20'
                newDocument['requestParameters']['timeout'] = '10000'
                newDocument['requestParameters']['retries'] = '3'
                newDocument['additionalData'] = dict()
                newDocument['additionalData']['CANAL'] = document['SO_CANAL']
                newDocument['additionalData']['CODIGO_TDT'] = document['CODIGOTDT']
                newDocument['additionalData']['NOME'] = document['SONDA_FULLNAME']
                if 'SUBSET' in document.keys():
                    newDocument['additionalData']['SUBSET'] = document['SUBSET']
                    newDocument['neName'] = '{0}-{1}'.format(document['NET_ADD'], document['SUBSET'])
                else:
                    newDocument['neName'] = document['NET_ADD']

                newDocument['ip'] = document['NET_ADD']
                newDocument['port'] = document['PORT']
                newDocument['collectable'] = "true"

                newDocument['hostId'] = document['NET_ADD']

                newDocument['lastUpdated'] = datetime.now()
                newDocument['versionId'] = newDocument['lastUpdated']
                newDocument['model'] = document['MEDIATION_PACK']
                newDocument['vendor'] = document['NAMF_VENDOR']
                newDocument['community'] = document['COMMUNITY']

                if 'VERSION' not in document.keys():
                    newDocument['versionSnmp'] = 'v2c'
                elif str(document["VERSION"]).upper() in self.version_translation.keys():
                    newDocument['versionSnmp'] = self.version_translation[str(document["VERSION"]).upper()]
                else:
                    newDocument['versionSnmp'] = 'v2c'

                try:
                    self._mongoConnection.executeQuery({'query': {'neName': newDocument['neName']}, 'set': newDocument},
                                                       'upSert')
                except:
                    self._mongoConnection.executeQuery(newDocument, 'insert')

            f.close()
            # apagar pela data de update
            print self._mongoConnection.executeQuery({'lastUpdated': {"$lt": data}, "additionalData.NOME": {"$regex": '.*Sonda*'}},
                                                     'remove')

        except Exception as e:
            print e
            print ("Unable to process {0} due to {1}: ".format(fileName, e))

    def processExcitador(self, filePath, fileName):
        data = datetime.today()
        data = datetime.strptime('{0}-{1}-{2} 00:00:00'.format(data.year, data.month, data.day), '%Y-%m-%d %H:%M:%S')
        try:
            header = list()
            lineNum = 0
            f = open(filePath, 'r+')
            for line in reader(f, delimiter=';'):
                lineNum += 1
                if lineNum == 1:
                    # vendorIdDate = datetime.strptime(line[0].strip(), '%Y-%m-%d %H:%M:%S')
                    continue
                elif lineNum == 2:
                    continue
                if lineNum == 3:
                    header = line
                    continue

                document = dict(zip(header, line))
                newDocument = dict()
                newDocument['requestParameters'] = dict()
                newDocument['requestParameters']['bulkSize'] = '20'
                newDocument['requestParameters']['timeout'] = '10000'
                newDocument['requestParameters']['retries'] = '3'
                newDocument['additionalData'] = dict()
                newDocument['additionalData']['CANAL'] = document['CANAL']
                newDocument['additionalData']['CODIGO_TDT'] = document['CODIGOTDT']
                newDocument['additionalData']['NOME'] = document['EMISSOR_FULLNAME']
                if 'SUBSET' in document.keys():
                    newDocument['additionalData']['SUBSET'] = document['SUBSET']
                    newDocument['neName'] = '{0}-{1}'.format(document['IP'], document['SUBSET'])
                else:
                    newDocument['neName'] = document['IP']

                newDocument['ip'] = document['IP']
                newDocument['port'] = document['PORT']
                newDocument['collectable'] = "true"

                newDocument['hostId'] = document['IP']

                newDocument['lastUpdated'] = datetime.now()
                newDocument['versionId'] = newDocument['lastUpdated']
                newDocument['model'] = document['MEDIATION_PACK']
                newDocument['vendor'] = document['NAMF_VENDOR']
                newDocument['community'] = document['COMMUNITY']

                if 'VERSION' not in document.keys():
                    newDocument['versionSnmp'] = 'v2c'
                elif str(document["VERSION"]).upper() in self.version_translation.keys():
                    newDocument['versionSnmp'] = self.version_translation[str(document["VERSION"]).upper()]
                else:
                    newDocument['versionSnmp'] = 'v2c'

                try:
                    self._mongoConnection.executeQuery({'query': {'neName': newDocument['neName']}, 'set': newDocument},
                                                       'upSert')
                except:
                    self._mongoConnection.executeQuery(newDocument, 'insert')

            f.close()
            # apagar pela data de update
            print self._mongoConnection.executeQuery(
                {'lastUpdated': {"$lt": data}, "additionalData.NOME": {"$regex": '.*Excitador*'}}, 'remove')

        except Exception as e:
            print e
            print ("Unable to process {0} due to {1}: ".format(fileName, e))
