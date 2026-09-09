#!/usr/bin/env python

__version__ = '1.0'

__doc__ = '''
Example file:

SITE,SERVER,DATA_DESDE,DATA_ATE,VARIAVEL,VALOR
PE,B2B15_MS09,20200517_021500,20200517_023000,CPU usage,4
PE,B2B15_MS09,20200517_021500,20200517_023000,Memory usage,48
PE,B2B15_MS09,20200517_021500,20200517_023000,Disk ROOT usage,41
PE,B2B15_MS09,20200517_021500,20200517_023000,Disk mcom usage,43
PE,B2B15_MS09,20200517_021500,20200517_023000,Disk files usage,16
PE,B2B15_MS09,20200517_021500,20200517_023000,Disk var usage,12
'''

__authors__ = [
	"Version 1.0: bruno-e-silva <bruno-e-silva@alticelabs.com>"
]

import os
import re
from csv import reader
from datetime import datetime
import importlib

# Local libraries
BaseOperator = importlib.import_module("shelf.collectorprocess.operators.BaseOperator").BaseOperator
FamilyObject = importlib.import_module("shelf.collectorprocess.operators.FamilyObject").FamilyObject
BaseCommand = importlib.import_module("shelf.collectorprocess.operators.Readers.MAHINDRA.CSV.Operator").Command
logger = importlib.import_module("shelf.collectorprocess.logger").logger


# Command class that extends the base command defined in Operator.py
class Command(BaseCommand):

	def __init__(self):
		self._file_name_regex = re.compile(r'^.*(SERVER_STATS_|STA_SIGNALING_).*.csv')
		self._command_name = ''
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

		if "STA_SIGNALING" in fileName:
			self._command_name = "CI_SIPPROTOCOL"
		elif "SERVER_STATS" in fileName:
			self._command_name = "CI_SERVERRESOURCES"

		dataDocuments = dict()
		pkConsolidator = list()

		try:
			try:
				#Open file for reading
				f = open(filePath, 'r')
			except IOError:
				logger.warning("Could not open sample file \"{}\" in read mode: ".format(fileName))

			# Used to store the column names from the first line of each file
			column_names_list = None
			n_column_names = 0
			n_line = 0
			for line in reader(f,delimiter=','):
				n_line += 1

				# Collects column names from first line of file
				if n_line == 1:
					if len(line) == 0:
						logger.warning("No column names found in first line of file \"{0}\"".format(fileName), __file__)
						break

					column_names_list = [x.upper() for x in line]
					n_column_names = len(column_names_list)
					pkConsolidator = list(set(column_names_list)-set(['VALOR', 'VARIAVEL']))
					continue

				if not line:
					continue

				# Checks if number of values in row is the same as the announced columns in the first line
				if len(line) != n_column_names:
					logger.warning(
						"Number of values in line {0} is different than number of announced columns in sample \"{1}\"".format(n_line, fileName), __file__)
					continue

				document = dict(zip(column_names_list, line))
				pkValue = ''
				sep = ''
				for attr in pkConsolidator:
					pkValue = '{:s}{:s}{:s}'.format(pkValue,sep,document[attr])
					sep = '-'

				if pkValue not in dataDocuments.keys():
					dataDocuments[pkValue] = dict()
					for attr in pkConsolidator:
						dataDocuments[pkValue][attr] = document[attr]
				dataDocuments[pkValue][document['VARIAVEL'].upper().replace(' ','')] = document['VALOR']

			try:
				for pkValue in dataDocuments.keys():
					for key in dataDocuments[pkValue].keys():
						if self._dateRegex.match(dataDocuments[pkValue][key]):
							dataDocuments[pkValue][key] = self.convertDateTime(dataDocuments[pkValue][key], oldformat2)
						elif self._dateRegex2.match(dataDocuments[pkValue][key]):
							dataDocuments[pkValue][key] = self.convertDateTime(dataDocuments[pkValue][key].split('.')[0], oldformat3)
					try:
						data_time = FamilyObject.parseEnvelopeDataTime(dataDocuments[pkValue]["DATA_DESDE"])
					except ValueError as e:
						logger.warning("Could not build mediationEnvelope due to {0}: ".format(e), __file__)
						continue

					yield {"dataTime": data_time, "granularitySec": 15, "data": dataDocuments[pkValue]}
			except Exception, e:
				logger.warning("Unable to process {0} in unit {1} because wrong format => {2}".format(fileName, self._command_name, e), __file__)
		except IOError:
			logger.error("ERROR[self._command_name]: Could not open sample file {0} in read mode.".format(fileName))
