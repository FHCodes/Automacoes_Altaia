#!/usr/bin/env python

__version__ = '1.0'

__doc__ = '''
Example file:

CUSTOMER_ID;SERVICE_ID;SERVICE_NAME;SHORT_CODE
1001;1582;CINEBIGSH;3132090583
'''

__authors__ = [
				"Version 1.0: bruno-e-silva <bruno-e-silva@alticelabs.com>"
			]

import os
import re
from csv import reader
import importlib
from datetime import datetime

# Local libraries
BaseOperator = importlib.import_module("shelf.collectorprocess.operators.BaseOperator").BaseOperator
FamilyObject = importlib.import_module("shelf.collectorprocess.operators.FamilyObject").FamilyObject
BaseCommand = importlib.import_module("shelf.collectorprocess.operators.Readers.MAHINDRA.CSV.Operator").Command
logger = importlib.import_module("shelf.collectorprocess.logger").logger


# Command class that extends the base command defined in Operator.py
class Command(BaseCommand):

	def __init__(self):
		self._file_name_regex = re.compile(r'^(ServicesNames_).*.csv$')
		self._command_name = 'DISC_CanalInterativo_Services'
		self._lineSepRegex = re.compile(r'\t')
		self._dateRegex = re.compile(r"[0-9]{8}_[0-9]{6}")
		self._dateRegex2 = re.compile(r"^[0-9]{2}-[0-9]{2}-[0-9]{4}\s[0-9]{2}:[0-9]{2}:[0-9]{2}.*$")

	def convertDateTime(self, dt, oldformat):
		try:
			dt = datetime.strptime(dt, oldformat)
		except:
			logger.warning("Invalid datetime format")
		return datetime.strftime(dt, '%Y-%m-%d %H:%M:%S')

	@property
	def line_format(self):
		return self._line_format

	def parse(self, filePath):
		oldformat = '%Y%m%d%H%M%S'
		oldformat2 = '%Y%m%d_%H%M%S'
		oldformat3 = '%d-%m-%Y %H:%M:%S'

		fileName = os.path.basename(filePath)
		logger.debug("Parsing SERVER_STATS and STA_SIGNALING format, in file {0}".format(fileName))

		try:
			regex_fileName = re.search("^[0-9_]*(.*?)_([0-9]+).csv$", fileName)
			dt = regex_fileName.group(2)
			dt = self.convertDateTime(dt, '%Y%m%d%H%M%S')
			try:
				#Open file for reading
				f = open(filePath, 'r')
			except IOError:
				logger.warning("Could not open sample file \"{}\" in read mode: ".format(fileName))

			# Used to store the column names from the first line of each file
			column_names_list = None
			n_column_names = 0
			n_line = 0
			for line in reader(f,delimiter=';'):
				n_line += 1

				# Collects column names from first line of file
				if n_line == 1:
					if len(line) == 0:
						logger.warning(
							"No column names found in first line of file \"{0}\"".format(fileName), __file__)
						break

					column_names_list = [x.upper() for x in line]
					n_column_names = len(column_names_list)
					continue

				if not line:
					continue

				# Checks if number of values in row is the same as the announced columns in the first line
				if len(line) != n_column_names:
					logger.warning(
						"Number of values in line {0} is different than number of announced columns in sample \"{1}\"".format(n_line, fileName), __file__)
					continue

				document = dict(zip(column_names_list, line))
				for key in document.keys():
					if self._dateRegex.match(document[key]):
						document[key] = self.convertDateTime(document[key], oldformat2)
					elif self._dateRegex2.match(document[key]):
						document[key] = self.convertDateTime(document[key].split('.')[0], oldformat3)

				document['PROCESSDATE'] = dt
				document['DATASOURCE'] = fileName

				try:
					try:
						data_time = FamilyObject.parseEnvelopeDataTime(document["PROCESSDATE"])
					except ValueError as e:
						logger.warning("Could not build mediationEnvelope due to {0}: ".format(e), __file__)
						continue

					yield {"dataTime": data_time, "granularitySec": 900, "data": document}
				except Exception, e:
					logger.warning("Unable to process {0} in unit {1} because wrong format => {2}".format(fileName, self._command_name, e), __file__)
					continue
		except IOError:
			logger.error("ERROR[self._command_name]: Could not open sample file {0} in read mode.".format(fileName))
