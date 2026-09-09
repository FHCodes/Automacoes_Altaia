#!/usr/bin/env python

__doc__ = \
'''
	3GPP V5.0 Performance XML reader
'''

__version__ = '0.1'

__authors__ = [
				"Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>"
			]

# Native libraries
import importlib
from datetime import datetime, timedelta
from pytz import timezone
import pytz
import xml.etree.cElementTree as ET
import os, sys, re

# Local libraries
BaseOperator = importlib.import_module("shelf.collectorprocess.operators.BaseOperator").BaseOperator
FamilyObject = importlib.import_module("shelf.collectorprocess.operators.FamilyObject").FamilyObject
logger = importlib.import_module("shelf.collectorprocess.logger").logger

def copy_catalog(catalog_Path):
	it = ET.iterparse(catalog_Path, events=('start', 'end'))
	for _, el in it:
		if '}' in el.tag:
			el.tag = el.tag.split('}', 1)[1]  # strip all namespaces
	return it.root

def convertTimeZone(date):
	if '-' in date:
		d1 = datetime.strptime(date[:-6], '%Y-%m-%dT%H:%M:%S')
		d2 = datetime.strptime('0001-01-01 ' + date[-5:] + ':00', '%Y-%m-%d %H:%M:%S')
		t1 = datetime.strptime('0001-01-01 00:00:00', '%Y-%m-%d %H:%M:%S')
		return t1 + (d1 - d2)
	return datetime.strptime(date, '%Y-%m-%d %H:%M:%S')

class Operator(BaseOperator):

	#Class Constructor
	def __init__(self, operationParams, baseObject={}):
		BaseOperator.__init__(self, operationParams, baseObject=baseObject)

	def process(self, familyObj=FamilyObject(), baseObject={}):

		filesToProcess = familyObj.getFiles()
		familyObj.clearFiles()

		# Start processing files
		for filePath in filesToProcess:
			try:
				fileName =  os.path.basename(filePath)

				root = copy_catalog(filePath)
				# Get shared information
				beginTime = datetime.strftime(convertTimeZone(root.find('fileHeader').find('measCollec').get('beginTime')), '%Y-%m-%d %H:%M:%S')
				measData = root.find('measData')
				prefixDn = measData.find('managedElement').get('localDn')
				familyObj.setUnitID('GENERIC')
				for measInfo in measData.iter('measInfo'):
					baseDocument = dict()
					baseDocument['DURATION'] = re.sub(r'[a-zA-Z]', '', measInfo.find('granPeriod').get('duration'))
					baseDocument['BEGINTIME'] = beginTime
					baseDocument['ENDTIME'] = datetime.strftime(convertTimeZone(measInfo.find('granPeriod').get('endTime')), '%Y-%m-%d %H:%M:%S')

					measTypeList = list()
					for measType in measInfo.iter('measType'):
						measTypeList.append(measType.text.upper())

					for measValue in measInfo.iter('measValue'):
						familyObj.clearDocuments()
						baseDocument['MEASOBJLDN'] = prefixDn + ',' + re.sub(r', ', ',', measValue.get('measObjLdn'))

						data = list()
						for r in measValue.iter('r'):
							data.append(r.text)
						if len(data) == 0:
							continue
						newDocument = dict(zip(measTypeList,data))
						newDocument.update(baseDocument)

						try:
							data_time = FamilyObject.parseEnvelopeDataTime(newDocument['BEGINTIME'])
						except Exception as e:
							print e
							logger.warning("Could not build mediationEnvelope due to : {0}".format(e), __file__)
							continue
						data_document = {"dataTime": data_time, "granularitySec": newDocument['DURATION'], "data": newDocument}
						familyObj.addDocument(data_document)
						#self.convert(familyObj=familyObj)
						self.nextOp(familyObj=familyObj, baseObject=baseObject)
			except Exception as ex:
				logger.error("Exception occurred on file '{0}', due to {1}".format(os.path.basename(filePath), ex.message), __file__)
