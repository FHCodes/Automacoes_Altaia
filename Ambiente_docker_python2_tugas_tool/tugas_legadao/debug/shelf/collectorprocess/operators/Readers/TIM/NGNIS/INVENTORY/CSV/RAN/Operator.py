#!/usr/bin/env python
__version__ = '1.0'

__doc__ = '''
			TIM NGNIS INVENTORY CSV RAN Reader
		  '''

__authors__ = [
	"Version 1.0: Bruno Silva <bruno-e-silva@alticelabs.com>"
]

import os
import re
from subprocess import call
import pandas as pd
from datetime import datetime
import importlib
import csv

# Local libraries
BaseOperator = importlib.import_module("shelf.collectorprocess.operators.BaseOperator").BaseOperator
FamilyObject = importlib.import_module("shelf.collectorprocess.operators.FamilyObject").FamilyObject
logger = importlib.import_module("shelf.collectorprocess.logger").logger

class Operator(BaseOperator):

	# Class constructor
	def __init__(self, operationParams, baseObject={}):
		BaseOperator.__init__(self, operationParams, baseObject=baseObject)

		self._outPath = '/tmp/'
		if 'tmp_fs' in self.options:
			self._outPath = self._options['tmp_fs']

	def process(self, familyObj=FamilyObject(), baseObject={}):

		logger.debug("Reading NGNIS RAN Performance XML file' contents...", __file__)
		filePath = familyObj.getFiles()[0]
		matchCases = re.compile(r';')
		convertion = re.compile(r';(-*[0-9]*),([0-9]*);')
		familyObj.clearDocuments()

		familyObj.fileName = os.path.basename(filePath)
		print familyObj.fileName

		try:
			fOut = '{0}{1}{2}'.format(self._outPath, ('' if self._outPath.endswith('/') else '/'), familyObj.fileName)
			f = open(fOut, "w")
			call(["sed", 's/"//g ; s/\s*\;/\;/g ; s/\;\s*/\;/g ; s/\s*$//g', filePath], stdout=f )
			f.close()
			filePath = fOut
		except Exception as e:
			logger.warning("Could not clean file \"{0}\" due to: {1}".format(familyObj.fileName, e))

		try:
			#Tirar data do nome do ficheiro
			#fazer match com NGNIS_SITES_QUAL_20201207_014002.csv
			fileNameRegex = re.search(r'^(?P<unitID>.*)\_.*(?P<startTime>\d{8}_\d{6}).csv.*', familyObj.fileName)
			startTime = datetime.strptime(fileNameRegex.group('startTime'), "%Y%m%d_%H%M%S")
			startTime = datetime.strftime(startTime,"%Y-%m-%d %H:%M:%S")
			unitID = fileNameRegex.group('unitID')
			timestamp = None
			try:
				timestamp = familyObj.parseEnvelopeDataTime(startTime)
			except ValueError as e:
				logger.warning("Could not build mediationEnvelope due to {0}: ".format(e), __file__)
				return

			mapping = {"NGNIS_CELLS_QUAL": "NGNIS_CELLS", "NGNIS_SITES_QUAL": "NGNIS_SITES", "NGNIS_DEVICES_QUAL": "NGNIS_DEVICES", "NGNIS_ANTENAS": "NGNIS_ANTENAS"}
			familyObj.setUnitID(mapping[unitID])

			lineNum = 0
			tmp = ''
			for chunck in pd.read_csv(filePath, sep=';', iterator=True, chunksize=10000, quoting=csv.QUOTE_NONE, encoding='latin1', error_bad_lines=False, na_filter=False, low_memory=False, dtype=str):
				for date, row in chunck.T.iteritems():
					document = row.to_dict()
					document = {key:val for key, val in document.items() if val not in ['', None]}
					document['TIMESTAMP'] = startTime
					document['LINENUM'] = lineNum
					document['INTERVAL'] = 1440
					lineNum += 1
					familyObj.addDocument({"dataTime": timestamp, "granularitySec": document['INTERVAL'], "data": document})
				self.nextOp(familyObj=familyObj, baseObject=baseObject)
				familyObj.clearDocuments()

		except Exception as e:
			print e
			print ("Unable to process {0} due to {1}: ".format(familyObj.fileName, e))

		#Delete the temporary file
		try:
			os.remove(filePath)
		except Exception as e:
			logger.warning("Could not remove temporary file after processing \"{0}\"".format(filePath))