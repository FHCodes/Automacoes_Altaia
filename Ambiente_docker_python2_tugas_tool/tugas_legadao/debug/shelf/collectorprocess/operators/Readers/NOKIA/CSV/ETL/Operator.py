#!/usr/bin/env python

__doc__ = \
	'''
	NOKIA CORE ETL Performance CSV reader
'''

__version__ = '0.1'

__authors__ = [
	"Version 0.1: Paulo Gil <paulo-a-gil@alticelabs.com>"
]


from csv import reader
import os
import re
import importlib
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

		logger.debug("Reading NOKIA CORE ETL Performance CSV file' contents...", __file__)
		filePath = familyObj.getFiles()[0]

		familyObj.clearDocuments()

		# Get file's name to find the unitID
		fileName = os.path.basename(filePath)
		familyObj.setUnitID('ETL_STATS')

		fileNameRegex = re.search(r'^(?P<counterName>.+?)\.(?P<startTime>\d+?)\.csv', fileName)
		startTime = '{0} 00:00:00'.format(fileNameRegex.group('startTime'))
		startTime = datetime.strptime(startTime, "%d%m%Y %H:%M:%S")
		startTime = datetime.strftime(startTime,"%Y-%m-%d %H:%M:%S")

		familyObj.fileName = fileName
		try:
			# Open file for writing
			f = open(filePath, 'r')
		except IOError:
			logger.error(
				"Could not open sample file \"{0}\" in read mode: ".format(fileName), __file__)

		# Used to store the column names from the first line of each file
		columnListName = ['DSA_ID','COUNTERVALUE']
		firstLine = True

		for line in reader(f):

			# Collects column names from first line of file
			if firstLine == True:
				firstLine = False
				continue

			try:
				document = dict(zip(columnListName, line))
				document['STARTTIME'] = startTime
				document['COUNTERNAME'] = fileNameRegex.group('counterName')
				try:
					data_time = familyObj.parseEnvelopeDataTime(document["STARTTIME"])
				except ValueError as e:
					logger.warning("Could not build mediationEnvelope due to {0}: ".format(e), __file__)
					continue

				familyObj.addDocument({"dataTime": data_time, "granularitySec": 1440, "data": document})
				self.nextOp(familyObj=familyObj, baseObject=baseObject)
				familyObj.clearDocuments()

			except Exception, e:
				logger.warning("Unable to process {0} in unit {1} because wrong format => {2}".format(familyObj.fileName, unit_id, e), __file__)
				continue
