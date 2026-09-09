#!/usr/bin/env python

__doc__ = \
    '''
        TROPICO PBX GPON Performance CSV Reader
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
        logger.debug("Reading TROPICO PBX IMS CSV file contents...", __file__)
        filePath = familyObj.getFiles()[0] #caminho dos ficheiros
        familyObj.clearDocuments() #limpar documentos

        fileName = os.path.basename(filePath) #nome do ficheiro sem o caminho

        regex = re.search(r'MEDIDA_(?P<unitID>\w+)_(?P<startTime>\d{8}_\d{4}).*\.csv', fileName)

        unitID = regex.group('unitID').upper()
        #startTime = regex.group('startTime').upper()
        familyObj.setUnitID(unitID) #definir unitID
        familyObj.fileName = fileName #definir parametros nos objetos para saber qual ficheiro esta a ser usado

        try:
            # Open file for writing
            f = open(filePath, 'r')
        except IOError:
            logger.error("Could not open sample file \"{0}\" in read mode: ".format(fileName), __file__)

        firstLine=True

        #startTime = datetime.strptime(startTime, "%Y%m%d_%H%M")
        #startTime = datetime.strftime(startTime, "%Y-%m-%d %H:%M:%S")
        columnNames = []
        for line in reader(f, delimiter=';'):
            if firstLine == True:
                # Iteracao sobre os elementos da linha
                for element in line:
                    # Converte o elemento para maiusculas
                    element = element.upper()
                    # Adiciona o elemento a lista de colunas
                    columnNames.append(element)
                firstLine = False
                continue

            try:
                '''
                for idx, ele in enumerate(line):
                    ele = ele.strip()
                    line[idx] = ele
                '''
                line = [ele.strip() for ele in line]

                document = dict(zip(columnNames, line))

#                document['END TIME'] = datetime.utcfromtimestamp(et).strftime('%Y-%m-%d %H:%M:%S')
                document['GRANULARITYPERIOD'] = 5
                #document['DATA_HORA_INICIO'] = startTime

                try:
                    data_time = familyObj.parseEnvelopeDataTime(document['DATA_HORA_INICIO'])
                except ValueError as e:
                    logger.warning("Could not build mediationEnvelope due to {0}: ".format(e), __file__)
                    continue

                # envelope
                familyObj.addDocument({"dataTime": data_time, "granularitySec": document['GRANULARITYPERIOD']*60, "data": document})
                self.nextOp(familyObj=familyObj, baseObject=baseObject)
                familyObj.clearDocuments()
            except Exception, e:
                logger.warning("Unable to process {0} in unit {1} because wrong format => {2}".format(familyObj.fileName, unitID, e), __file__)
                continue
