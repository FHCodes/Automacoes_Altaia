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

	def process(self, familyObj=FamilyObject(), baseObject={}):
		granularityDef = json.load(open('/opt/alticelabs/namf/src/shelf/collectorprocess/operators/Readers/ONMOBILE/CSV/granularityConfig.json'))
		regex_filename="(\w+)_(\d+).csv"
		files_to_process = familyObj.getFiles()

		logger.debug("Reading ONMOBILE Performance CSV files' contents...", __file__)
		for filePath in files_to_process:

			#Get file's name to find the unitID
			fileName = os.path.basename(filePath)
			if os.path.getsize(filePath) == 0:
				logger.warning("The File \"{0}\" has 0 bytes".format(fileName))
				continue

			familyObj.clearDocuments()
			familyObj.fileName = fileName

			regexmatch=re.match(regex_filename, familyObj.fileName)
			if regexmatch == None:
				logger.warning("Filename not expected \"{0}\" ".format(fileName))
				continue

			#Get the unit from the filename
			unitID=regexmatch.group(1).upper()

			#set unitID obtained in filename
			familyObj.setUnitID(unitID)


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

				# Collects column names from first line of file
				if n_line == 1:
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
				document["DATE_TIME"]= document["DATE"] + ' ' + document["TIME"].replace('AM','').replace('PM','')

				# Define granularity with unitId as base
				if unitID not in granularityDef.keys():
					continue
				document["GRANULARITYPERIOD"] = granularityDef[unitID]

				# Vendor request
				if "DISK_PARTION_UTILIZATION" in document.keys():
					document["DISK_PARTION_UTILIZATION"] = document["DISK_PARTION_UTILIZATION"].replace('%','')

				try:
					try:
						data_time = familyObj.parseEnvelopeDataTime(document["DATE_TIME"])
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
