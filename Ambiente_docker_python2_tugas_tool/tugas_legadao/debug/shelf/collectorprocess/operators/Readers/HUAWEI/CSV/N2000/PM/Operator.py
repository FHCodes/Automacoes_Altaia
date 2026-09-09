#!/usr/bin/env python

__doc__ = \
	'''
	Huawei N2000 Performance CSV reader
'''

__version__ = '0.1'

__authors__ = [
	"Version 0.1: Francisco Santiago <francisco-j-santiago@telecom.pt>"
	"Version 1.1: Ricardo Auxiliar <ricardo-d-auxiliar@alticelabs.com>"
]

# Native libraries
from csv import reader
import os
from datetime import datetime, timedelta
import importlib

# Local libraries
BaseOperator = importlib.import_module("shelf.collectorprocess.operators.BaseOperator").BaseOperator
FamilyObject = importlib.import_module("shelf.collectorprocess.operators.FamilyObject").FamilyObject
logger = importlib.import_module("shelf.collectorprocess.logger").logger


class Operator(BaseOperator):

	# Class Constructor
	def __init__(self, operationParams, baseObject={}):
		BaseOperator.__init__(self, operationParams, baseObject=baseObject)
		# Initialize start time calculator flag according to spec file
		self.convert_collecttime = True
		if "convert_collecttime" in self.options:
			if self.options["convert_collecttime"].upper() == "FALSE":
				self.convert_collecttime = False

	def process(self, familyObj=FamilyObject(), baseObject={}):

		files_to_process = familyObj.getFiles()

		logger.debug("Reading Huawei N2000 Performance CSV files' contents...", __file__)
		for filePath in files_to_process:

			familyObj.clearDocuments()

			# Get file's name to find the unitID
			file_name = os.path.basename(filePath)
			familyObj.fileName = file_name

			try:
				# Open file for writing
				f = open(filePath, 'r')
			except IOError:
				logger.error(
					"Could not open sample file \"{0}\" in read mode: ".format(
						file_name), __file__)
				continue

			# Used to store the column names from the first line of each file
			column_names_list = None
			n_column_names = 0

			for n_line, line in enumerate(reader(f)):

				familyObj.clearDocuments()

				# Collects family id from first line of file
				if n_line == 0:
					try:
						unit_id = line[0].upper()
						familyObj.setUnitID(unit_id)
						continue
					except IndexError as e:
						logger.warning(
							"Could not find Unit ID in sample due to {0}".format(e), __file__)
						break

				# Used to store the column names from the second line of each file
				if n_line == 1:
					if len(line) == 0:
						logger.warning(
							"No column names found in first line of file \"{0}\"".format(
								file_name), __file__)
						break

					column_names_list = [x.strip().upper() for x in line]
					n_column_names = len(column_names_list)
					continue

				# Checks if number of values in row is the same as the announced columns in the second line
				if len(line) != n_column_names:
					logger.warning(
						"Number of values in line {0} is different than number of announced columns in sample "
						"\"{1}\"".format(n_line, file_name), __file__)
					continue

				document = dict(zip(column_names_list, line))

				try:
					try:
						collection_time = datetime.strptime(document["COLLECTION TIME"], "%Y-%m-%d %H:%M:%S")
						polling_period = document["POLLING PERIOD"]
						# polling period in hours to calculate timedelta
						polling_period_hours = timedelta(minutes=int(polling_period))
						if self.convert_collecttime:
							# calculate collection time
							dt = collection_time - polling_period_hours
							# datetime to Oracle
							document["COLLECTION TIME"] = str(dt)
						# datetime to Envelope
						collection_time = familyObj.parseEnvelopeDataTime(str(document["COLLECTION TIME"]))
						granularity_sec = str(int(polling_period) * 60)
						granularity_sec = familyObj.parseEnvelopeGranularitySec(granularity_sec)
					except ValueError as e:
						logger.warning(
							"Could not build mediationEnvelope due to {0}: ".format(
								e), __file__)
						continue

					familyObj.addDocument(
						{"dataTime": collection_time, "granularitySec": granularity_sec, "data": document})

					self.nextOp(familyObj=familyObj, baseObject=baseObject)
				except Exception, e:
					logger.warning(
						"Unable to process {0} in unit {1} because wrong format => {2}".format(
							familyObj.fileName, unit_id, e), __file__)
					continue
