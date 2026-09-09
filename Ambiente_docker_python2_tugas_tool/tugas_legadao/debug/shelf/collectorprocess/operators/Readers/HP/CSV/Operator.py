#!/usr/bin/env python

__doc__ = \
	'''
	ONMOBILE RBT Performance CSV reader
'''

__version__ = '1.2'

__authors__ = [
	"Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>"
]


from csv import reader
import os
import re
import time
import importlib
import json

# Local libraries
BaseOperator = importlib.import_module("shelf.collectorprocess.operators.BaseOperator").BaseOperator
FamilyObject = importlib.import_module("shelf.collectorprocess.operators.FamilyObject").FamilyObject
logger = importlib.import_module("shelf.collectorprocess.logger").logger


class Operator(BaseOperator):

	# Class Constructor
	def __init__(self, operationParams, baseObject={}):
		BaseOperator.__init__(self, operationParams, baseObject=baseObject)

	def strfileToDate(self,s):
		timeStruct = time.strptime(s, "%Y%m%d%H%M%S")
		timeString = time.strftime("%Y-%m-%d %H:%M:%S", timeStruct)
		return timeString

	def process(self, familyObj=FamilyObject(), baseObject={}):

		granularityDef = json.load(open('/opt/alticelabs/namf/src/shelf/collectorprocess/operators/Readers/HP/CSV/granularityConfig.json'))
		files_to_process = familyObj.getFiles()
		logger.debug("Reading HP LBS RBT Performance CSV files' contents...", __file__)

		for filePath in files_to_process:
			fileName = os.path.basename(filePath)
			familyObj = FamilyObject()
			familyObj.fileName = fileName
			familyObj.clearDocuments()

			#Get file's name to find the unitID
			if os.path.getsize(filePath) == 0:
				logger.warning("The File \"{0}\" has 0 bytes".format(fileName))
				continue

			regexmatch = re.match("(.*)_(\d{12})_(\d{12})", fileName)

			#try:
			unitID = regexmatch.group(1).upper()
			familyObj.setUnitID(unitID)
			data_ini = regexmatch.group(2)
			data_fim = regexmatch.group(3)
			date = self.strfileToDate(data_ini)

			try:
				#Open file for reading
				f = open(filePath, 'r')
			except IOError:
				logger.warning("Could not open sample file \"{}\" in read mode: ".format(fileName))
				continue

			# Used to store the column names from the first line of each file
			column_names_list = None
			n_column_names = 0
			n_line = 0
			for line in reader(f,delimiter=','):

				familyObj.clearDocuments()

				n_line += 1

				if n_line <= 4:
					continue

				# Collects column names from first line of file
				if n_line == 5:
					if len(line) == 0:
						logger.warning(
							"No column names found in first line of file \"{0}\"".format(file_name), __file__)
						break

					column_names_list = [x.upper() for x in line]
					n_column_names = len(column_names_list)
					continue

				if not line:
					continue

				# Checks if number of values in row is the same as the announced columns in the first line
				if len(line) != n_column_names:
					logger.warning(
						"Number of values in line {0} is different than number of announced columns in sample \"{1}\"".format(n_line, file_name), __file__)
					continue

				document = dict(zip(column_names_list, line))
				document["STARTTIME"] = date

				# Define granularity with unitId as base
				if unitID not in granularityDef.keys():
					continue
				document["GRANULARITYPERIOD"] = granularityDef[unitID]

				try:
					try:
						data_time = familyObj.parseEnvelopeDataTime(document["STARTTIME"])
						granularity_sec = familyObj.parseEnvelopeGranularitySec(int(document["GRANULARITYPERIOD"]))
					except ValueError as e:
						logger.warning("Could not build mediationEnvelope due to {0}: ".format(e), __file__)
						continue

					familyObj.addDocument({"dataTime": data_time, "granularitySec": granularity_sec, "data": document})

					# Final operations to the fields with timestamp and granularity period

					self.nextOp(familyObj=familyObj, baseObject=baseObject)
				except Exception, e:
					logger.warning("Unable to process {0} in unit {1} because wrong format => {2}".format(familyObj.fileName, unitID, e), __file__)
					continue
