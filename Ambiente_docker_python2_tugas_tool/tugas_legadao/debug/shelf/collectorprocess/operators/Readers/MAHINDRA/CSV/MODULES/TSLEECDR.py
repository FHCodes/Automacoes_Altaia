#!/usr/bin/env python

__version__ = '1.0'

__doc__ = '''
Example file:

SessionId;CallId;B2BInstance;IVRInstance;SessionStart;SessionEnd;Answer;IVRRelease;TransferStart;SessionDuration;IVRCallDuration;TransferredCallDuration;CallingPN;CalledPN;CallTransferTriesQtty;CallTransferPN;B2BStatusCode;B2BStatusDescription;SIPFinalResponseCode;CallDirection;AppName;AppVersion
1153378901;4dy5b2qa2fbcd4j5a59q4bcjn9ycqb5e@SoftX3000;FE13;MS04;17-05-2020 05:27:59.000000;17-05-2020 05:28:16.000000;17-05-2020 05:27:59.000000;17-05-2020 05:28:16.000000000;;17;17;;5432325977;2124612069;;;0;OK;200 OK;IC;B2BUA;1-0-0-99
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
		self._file_name_regex = re.compile(r'^\d+?_(TSLEECDR_ALTAIA).*.csv$')
		self._command_name = 'CI_CALLSATTEMPTSCDR'
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

				if not line and line == '':
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

				try:
					if document['CALLDIRECTION'] == 'IC':
						document['SHORTCODE'] = document['CALLEDPN']
					elif document['CALLDIRECTION'] == 'OG':
						document['SHORTCODE'] = document['CALLINGPN']
					else:
						document['SHORTCODE'] = ''
				except:
					document['SHORTCODE'] = ''

				try:
					try:
						data_time = FamilyObject.parseEnvelopeDataTime(document["SESSIONSTART"])
					except ValueError as e:
						logger.warning("Could not build mediationEnvelope due to {0}: ".format(e), __file__)
						continue

					yield {"dataTime": data_time, "granularitySec": 15, "data": document}
				except Exception, e:
					logger.warning("Unable to process {0} in unit {1} because wrong format => {2}".format(fileName, self._command_name, e), __file__)
					continue
		except IOError:
			logger.error("ERROR[self._command_name]: Could not open sample file {0} in read mode.".format(fileName))
