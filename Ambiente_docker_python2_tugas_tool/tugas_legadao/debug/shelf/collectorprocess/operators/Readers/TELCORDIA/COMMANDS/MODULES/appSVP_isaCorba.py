#!/usr/bin/env python

__version__ = '1.0'

__doc__ = '''
Example file:

'''

__authors__ = [
				"Version 1.0: bruno-e-silva <bruno-e-silva@alticelabs.com>"
			]

from csv import reader
from datetime import date, timedelta
import os
import json
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
		self._file_name_regex = re.compile(r'^(APPSVR_MEAS_|ISA_CORBA_).*$')
		self._command_name = ''
		self._lineSepRegex = re.compile(r'\t')

	@property
	def line_format(self):
		return self._line_format

	def parse(self, file_path):
		counters_for_family = json.load(open('/opt/alticelabs/namf/src/shelf/collectorprocess/operators/Readers/TELCORDIA/COMMANDS/MODULES/mappingCounterforFamily.json'))
		listIndexToRemove = [7,5,2,1]
		logger.debug("Parsing TELCORDIA format, in file {0}".format(os.path.basename(file_path)))
		file_name = os.path.basename(file_path)

		# Open file for reading
		try:
			f = open(file_path)
			for line in reader(f,delimiter=','):
				#Join positions 4 and 5 of row to concat date and time of start of measurement
				line[4] = line[4].replace("/","-") + " " + line[5] + ":00"
				#Join positions 4 and 5 of row to concat date and time of end of measurement
				line[6] = line[6].replace("/","-") + " " + line[7] + ":00"

                                for i in listIndexToRemove:
                                        del line[i]

				if line[0] == 'APPSVR_MEAS':
					familyId = line[4].upper()
					del line[0]
				else:
					familyId = 'ISA_CORBA'

				if familyId not in counters_for_family.keys():
					continue

				self._command_name = familyId
				document = dict(zip(counters_for_family[familyId][:len(line)], line))
				document['GRANULARITY_PERIOD'] = 1440
                                document['OSP'] = document['HOSTNAME']
				#print document
				#return
				try:
					# Parse the date
					data_time = FamilyObject.parseEnvelopeDataTime(document['RESULT_TIME_END'])
				except ValueError as e:
					logger.error("Could not build mediationEnvelope due to {0}: ".format(e), __file__)
					continue

				yield {"dataTime": data_time, "granularitySec": document['GRANULARITY_PERIOD'], "data": document}

		except IOError:
			logger.error("ERROR[BSC]: Could not open sample file {0} in read mode.".format(os.path.basename(file_path)))
