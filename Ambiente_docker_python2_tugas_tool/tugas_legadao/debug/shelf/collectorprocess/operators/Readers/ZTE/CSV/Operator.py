#!/usr/bin/env python

__doc__ = \
    '''
        ZTE U31 GPON Performance CSV Reader
    '''

__version__ = '0.1'

__authors__ = [
    "Version 0.1: Pedro Silva <pedro-c-silva@alticelabs.com>"
]

#import sys #remover quando passa a namf
from csv import reader
import re
import os
from datetime import datetime
#imports namf
import importlib

# Local libraries
BaseOperator = importlib.import_module("shelf.collectorprocess.operators.BaseOperator").BaseOperator
FamilyObject = importlib.import_module("shelf.collectorprocess.operators.FamilyObject").FamilyObject
logger = importlib.import_module("shelf.collectorprocess.logger").logger

#fileName = sys.argv[1] #remover quando passa a namf

class Operator(BaseOperator):

    # Class Constructor
    def __init__(self, operationParams, baseObject={}):
        BaseOperator.__init__(self, operationParams, baseObject=baseObject)

    def process(self, familyObj=FamilyObject(), baseObject={}): #para o namf chamar a classe
        logger.debug("Reading ZTE U31 GPON CSV file contents...", __file__)
        #filePath = familyObj.getFiles()[0] #caminho dos ficheiros
        filesToProcess = familyObj.getFiles()
        familyObj.clearDocuments() #limpar documentos

        for filePath in filesToProcess:
            fileName = os.path.basename(filePath) #nome do ficheiro sem o caminho

            regex = re.search(r'ZTE_U31_(?P<unitID>\w+?)_.*\.csv',fileName)

            unitID = regex.group('unitID').upper()
            familyObj.setUnitID(unitID) #definir unitID
            familyObj.fileName = fileName #definir parametros nos objetos para saber qual ficheiro esta a ser usado

            try:
                # Open file for writing
                f = open(filePath, 'r')
            except IOError:
                logger.error("Could not open sample file \"{0}\" in read mode: ".format(fileName), __file__)

            firstLine=True

            for line in reader(f, delimiter=','):
                if firstLine == True:
                    columnNames = [element.upper() for element in line]
                    firstLine = False
                    continue

                try:
                    document = dict(zip(columnNames, line))
                    st = int(document['START TIME'])/1000
                    et = int(document['END TIME']) / 1000
                    document['START TIME'] = datetime.utcfromtimestamp(st).strftime('%Y-%m-%d %H:%M:%S')
                    document['END TIME'] = datetime.utcfromtimestamp(et).strftime('%Y-%m-%d %H:%M:%S')
                    document['GRANULARITYPERIOD'] = 15

                    try:
                        data_time = familyObj.parseEnvelopeDataTime(document['START TIME'])
                    except ValueError as e:
                        logger.warning("Could not build mediationEnvelope due to {0}: ".format(e), __file__)
                        continue

                    # envelope
                    familyObj.addDocument({"dataTime": data_time, "granularitySec": 15, "data": document})
                    self.nextOp(familyObj=familyObj, baseObject=baseObject)
                    familyObj.clearDocuments()
                except Exception, e:
                    logger.warning("Unable to process {0} in unit {1} because wrong format => {2}".format(familyObj.fileName, unitID, e), __file__)
                    continue
