#!/usr/bin/env python

__version__ = '1.0'

__doc__ = '''
Example file:

'''

__authors__ = [
				"Version 1.0: bruno-e-silva <bruno-e-silva@alticelabs.com>"
			]

from csv import reader
from datetime import date, timedelta, datetime
import time
import os
import re
import copy
import importlib

# Local libraries
BaseOperator = importlib.import_module("shelf.collectorprocess.operators.BaseOperator").BaseOperator
FamilyObject = importlib.import_module("shelf.collectorprocess.operators.FamilyObject").FamilyObject
BaseCommand = importlib.import_module("shelf.collectorprocess.operators.Readers.ALCATEL.COMMANDS.Operator").Command
logger = importlib.import_module("shelf.collectorprocess.logger").logger

# Command class that extends the base command defined in Operator.py
class Command(BaseCommand):

	def __init__(self):
		self._file_name_regex = re.compile(r'^ismo_measure\..*\.GDI\.CSV$')
		self._command_name = 'ISMO_MEASURE_GDI'
		self._lineSepRegex = re.compile(r'\t')

	@property
	def line_format(self):
		return self._line_format

	def parse(self, file_path):
		logger.debug("Parsing TELCORDIA format, in file {0}".format(os.path.basename(file_path)))

		file_name = os.path.basename(file_path)
		resulttime = file_name.split('.')[1]
		resulttime = '{:s}-{:s}-{:s}'.format(resulttime[0:4], resulttime[4:6], resulttime[6:8])

		# Open file for reading
		try:
			f = open(file_path)
			header = list()
			for line in reader(f,delimiter=','):
				if header == list():
					header = line
					for i, elem in enumerate(header):
						if elem == 'Processor':
							header[i] = 'HOSTNAME'
						elif elem == 'Hour Ending at':
							header[i] = 'RESULT_TIME'
					header = [x.upper() for x in header]
					continue
				elif 'N/A' in line:
					continue
				document = dict(zip(header,line))
				document['GRANULARITY_PERIOD'] = 1440

				if '24' in document['RESULT_TIME']:
					t = time.strptime(resulttime, "%Y-%m-%d")
					newDate = date(t.tm_year,t.tm_mon,t.tm_mday) + timedelta(1)
					document['RESULT_TIME'] = '{:s} {:s}:00'.format(newDate.strftime('%Y-%m-%d'), document['RESULT_TIME'].replace('24', '00'))

				else:
					document['RESULT_TIME'] = '{:s} {:s}:00'.format(resulttime, document['RESULT_TIME'])

				try:
					# Parse the date
					data_time = FamilyObject.parseEnvelopeDataTime(document['RESULT_TIME'])
				except ValueError as e:
					logger.error("Could not build mediationEnvelope due to {0}: ".format(e), __file__)
					continue

				yield {"dataTime": data_time, "granularitySec": document['GRANULARITY_PERIOD'], "data": document}

		except IOError:
			logger.error("ERROR[BSC]: Could not open sample file {0} in read mode.".format(os.path.basename(file_path)))
