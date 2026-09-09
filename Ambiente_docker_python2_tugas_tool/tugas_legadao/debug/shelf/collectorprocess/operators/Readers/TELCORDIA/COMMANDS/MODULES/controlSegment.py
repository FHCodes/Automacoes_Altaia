#!/usr/bin/env python

__version__ = '1.0'

__doc__ = '''

'''

__authors__ = [
	"Version 1.0: bruno-e-silva <bruno-e-silva@alticelabs.com>"
]

import os
import re
import importlib

# Local libraries
BaseOperator = importlib.import_module("shelf.collectorprocess.operators.BaseOperator").BaseOperator
FamilyObject = importlib.import_module("shelf.collectorprocess.operators.FamilyObject").FamilyObject
BaseCommand = importlib.import_module("shelf.collectorprocess.operators.Readers.TELCORDIA.COMMANDS.Operator").Command
logger = importlib.import_module("shelf.collectorprocess.logger").logger


# Command class that extends the base command defined in Operator.py
class Command(BaseCommand):

	def __init__(self):
		self._file_name_regex = re.compile(r'^ControlSegmentUsage\..*\.out$')
		self._command_name = 'CONTROLSEGMENTUSAGE'
		self._regex = re.compile(r'^(?P<hostname>.*?)\s+(?P<CONTROL_SEGMENTS_USAGE>.+?)$')

	@property
	def line_format(self):
		return self._line_format

	def parse(self, file_path):
		logger.debug("Parsing BSC format, in file {0}".format(os.path.basename(file_path)))
		regexHostName = re.compile(r'^1\: Summary of Records Received  on  (?P<hostname>.*?)$')
		file_name = os.path.basename(file_path)
		try:
			resulttime = file_name.split('.')[1]
			resulttime = '{:s}-{:s}-{:s} 00:00:00'.format(resulttime[0:4], resulttime[4:6], resulttime[6:8])
		except:
			logger.error("ERROR[TELCORDIA_CPLISTREPORT]: Could not get date from fileName {0}.".format(os.path.basename(file_path)))
			return

		hostname = ''
		# Open file for reading
		try:
			f = open(file_path)
			lines = f.readlines()
			f.close()

			while len(lines) > 0:
				line = lines.pop(0).strip('\n|\r')
				if line == '':
					continue

				data = self._regex.match(line)
				document = dict()
				document['RESULT_TIME'] = resulttime
				document['HOSTNAME'] = data.group('hostname')
				document['CONTROL_SEGMENTS_USAGE'] = data.group('CONTROL_SEGMENTS_USAGE')
				document['GRANULARITY_PERIOD'] = 1440

				try:
					# Parse the date
					data_time = FamilyObject.parseEnvelopeDataTime(document['RESULT_TIME'])
				except ValueError as e:
					logger.error("Could not build mediationEnvelope due to {0}: ".format(e), __file__)
					continue

				yield {"dataTime": data_time, "granularitySec": document['GRANULARITY_PERIOD'], "data": document}

		except IOError:
			logger.error("ERROR[TELCORDIA_CPLISTREPORT]: Could not open sample file {0} in read mode.".format(os.path.basename(file_path)))
