#!/usr/bin/env python

__version__ = '1.0'

__doc__ = '''
	SIEMENS ASN1 Performance reader

Example file:

Successful Internal Handovers per BSC per cause	(0,0)	2020-05-10 12:00:00-03:00	bsc {35	0}	90	BSS:35/SCANBSC:0	60	1	0	0	0	694 2765 1756 1326 0 4850 43 0 0 0 0 3 0 0 0 0 0 6899
Total number of Handover failures Intra BSC	(0,14)	2020-05-10 12:00:00-03:00	bsc {35	0}	90	BSS:35/SCANBSC:0	60	1	0	0	0	2378
Number of Inter BSC Handover failures	(0,15)	2020-05-10 12:00:00-03:00	bsc {35	0}	90	BSS:35/SCANBSC:0	60	1	0	0	0	4
'''

__authors__ = [
				"Version 1.0: bruno-e-silva <bruno-e-silva@alticelabs.com>"
			]

import os
import json
import re
import copy
from datetime import datetime
import importlib

# Local libraries
BaseOperator = importlib.import_module("shelf.collectorprocess.operators.BaseOperator").BaseOperator
FamilyObject = importlib.import_module("shelf.collectorprocess.operators.FamilyObject").FamilyObject
BaseCommand = importlib.import_module("shelf.collectorprocess.operators.Readers.MAHINDRA.CSV.Operator").Command
logger = importlib.import_module("shelf.collectorprocess.logger").logger



class Operator(BaseOperator):

	#Class Constructor
	def __init__(self, operationParams, baseObject={}):
		BaseOperator.__init__(self, operationParams, baseObject=baseObject)
		self.unitList= json.load(open('/opt/alticelabs/namf/src/shelf/collectorprocess/operators/Readers/SIEMENS/ASCII/tableMapping.json'))


	def process(self, familyObj=FamilyObject(), baseObject={}):

		filesToProcess = familyObj.getFiles()
		familyObj.clearDocuments()
		lineRegex = re.compile(r'(\w+? \{(\d|\t)*\})|([^ \t][^\t]*[\t]*)')

		logger.debug("[Reader] Reading SIEMENS ASN1 Performance files' contents...")

		for filePath in filesToProcess:
			#Get file's name
			fileName = os.path.basename(filePath)
			familyObj = FamilyObject()
			familyObj.fileName = fileName

			try:
				#Open file for reading
				f = open(filePath, 'r')
			except IOError:
				logger.warning("Could not open sample file \"{}\" in read mode: ".format(fileName))
				continue

			for line in f.readlines():

				if not line or line == '':
					continue

				temp = re.findall(lineRegex, line)
				if temp == None:
					continue

				lineData = list()
				for x, y, z in temp:
					if x != '':
						lineData.append(x.replace('\t',' ').strip())
					elif y != '':
						lineData.append(y.replace('\t',' ').strip())
					elif z != '':
						lineData.append(z.replace('\t',' ').strip())

				if lineData != []:
					unitID = '{:s}{:s}'.format(lineData[1], lineData[-2])
					headerData = dict()
					headerData['RESULT_TIME'] = lineData[2][:-6]
					headerData['MONITORED_OBJECT_INSTANCE'] = lineData[3]
					headerData['OMC_RELEASE_VERSION'] = lineData[4]
					headerData['SCANNER_FDN'] = lineData[5]
					headerData['GRANULARITYPERIOD'] = lineData[6]

					objectResultNumber = int(lineData[7])

				counters = lineData[-1].split(' ')
				numberOfCounters = len(counters)/objectResultNumber
				for index in xrange(objectResultNumber):
					document = copy.deepcopy(headerData)
					document['OBJECT_TYPE'] = document['MONITORED_OBJECT_INSTANCE'].split(' ')[0].upper()
					document['SEC_OBJECT'] = lineData[8+index]
					if '{' not in document['SEC_OBJECT']:
						document['SEC_OBJECT'] = 'NO_OBJECT'

					if unitID in self.unitList.keys():
						for counterId in self.unitList[unitID]:
							document[counterId] = counters.pop(0)
					match = re.match(r".*\s+(\d+)\}\s*$", document['MONITORED_OBJECT_INSTANCE'])
					if match:
						document['OBJECT_SYMBOLIC_NAME'] = '{:s}/{:s}:{:s}'.format(document['SCANNER_FDN'].split('/')[0],document['OBJECT_TYPE'],match.groups()[0].upper())
					familyObj.clearDocuments()
					newFamilyObject=FamilyObject()
					newFamilyObject.fileName = familyObj.fileName
					newFamilyObject.setUnitID(unitID)

					try:
						data_time = FamilyObject.parseEnvelopeDataTime(document["RESULT_TIME"])
					except ValueError as e:
						logger.warning("Could not build mediationEnvelope due to : {0}".format(e), __file__)
						continue
					data_document = {"dataTime": data_time, "granularitySec": int(headerData['GRANULARITYPERIOD']), "data": document}
					newFamilyObject.addDocument(data_document)

					self.nextOp(familyObj=newFamilyObject, baseObject=baseObject)
