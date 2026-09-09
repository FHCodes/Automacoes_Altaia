#!/usr/bin/env python

__doc__ = \
	'''
	Huawei NCE Performance CSV reader
'''

__version__ = '1.3'

__authors__ = [
	"Version 0.1: Francisco Santiago <francisco-j-santiago@telecom.pt>",
	"Version 1.1: Joao Pio <joao-t-pio@telecom.pt>",
	"Version 1.2: Bruno Silva <bruno-e-silva@alticelabs.com>",
	"Version 1.3: Gil Martins <gil-l-martins@alticelabs.com>"
]


import csv
import os
import re
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

	def process(self, familyObj=FamilyObject(), baseObject={}):

		filesToProcess = familyObj.getFiles()
		familyObj.clearDocuments()

		logger.debug("[Reader] Reading Huawei Performance IG CSV files' contents...")

		for filePath in filesToProcess:

			# Get file's name to find the unitID
			fileName = os.path.basename(filePath)

			familyObj = FamilyObject()
			familyObj.fileName = fileName
			try:
				# Set unitID
				familyObj.unitID = re.match(r"^PM_(?P<unitID>\w+?)_.*.csv$", fileName).group("unitID").upper()
			except Exception as e:
				logger.warning(e)
				logger.warning("Could not extract unit ID of name in sample file \"{}\"  ".format(fileName))
				continue
			try:
				# Open file for writing
				f = open(filePath, 'r')
			except IOError:
				logger.warning("Could not open sample file \"{}\" in read mode: ".format(fileName))
				continue

			# Used to store the column names from the first line of each file
			header = None
			n_header = 0
			n_line = 0
			try:
				for line in csv.reader(f, delimiter=','):
					n_line += 1

					if n_line == 1:
						continue

					# Collects column names from file header
					if n_line == 2:
						if len(line) == 0:
							logger.warning("No column names found in first line of file \"{0}\"".format(fileName))
							break

						header = [col.upper() for col in line]
						n_header = len(header)
						continue

					# If line corresponds to values
					line = [value.strip() for value in line]

					# Checks if number of values in row is the same as the announced columns in the first line
					if len(line) != n_header:
						logger.warning("Number of values in line {0} is different than number of announced columns in sample \"{1}\"".format(n_line, fileName))
						continue

					try:
						document = dict(zip(header, line))

						# if header had an empty column (last element, if line ends with ',')
						try:
							del document['']
						except KeyError:
							pass

						granularity = int(document["GRANULARITYPERIOD"])

						# convert epoch to timestamp (end time) and subtract granularity period to obtain start time
						document['COLLECTIONTIME'] = datetime.utcfromtimestamp(int(document['COLLECTIONTIME'])/1000)
						document['STARTTIME'] = (document['COLLECTIONTIME'] - timedelta(minutes=granularity)).strftime('%Y-%m-%d %H:%M:%S')
						document['COLLECTIONTIME'] = document['COLLECTIONTIME'].strftime('%Y-%m-%d %H:%M:%S')

						try:
							data_time = familyObj.parseEnvelopeDataTime(document['STARTTIME'])
						except ValueError as e:
							logger.warning("Could not build mediationEnvelope due to {0}: ".format(e), __file__)
							continue

						familyObj.addDocument({"dataTime": data_time, "granularitySec": granularity * 60, "data": document})
						self.nextOp(familyObj=familyObj, baseObject=baseObject)
						familyObj.clearDocuments()

					except Exception, e:
						logger.warning(
							"Unable to process {0} in unit {1} because wrong format => {2}".format(familyObj.fileName, familyObj.unitID, e), __file__)
						continue

			except csv.Error, e:
				logger.warning("{0} in file '{1}'.".format(e, fileName))
