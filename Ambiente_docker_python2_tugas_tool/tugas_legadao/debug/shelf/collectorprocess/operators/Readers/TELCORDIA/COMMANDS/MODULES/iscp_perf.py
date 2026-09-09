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
import re
import copy
import json
import importlib

# Local libraries
BaseOperator = importlib.import_module("shelf.collectorprocess.operators.BaseOperator").BaseOperator
FamilyObject = importlib.import_module("shelf.collectorprocess.operators.FamilyObject").FamilyObject
BaseCommand = importlib.import_module("shelf.collectorprocess.operators.Readers.ALCATEL.COMMANDS.Operator").Command
logger = importlib.import_module("shelf.collectorprocess.logger").logger

# Command class that extends the base command defined in Operator.py
class Command(BaseCommand):

	def __init__(self):
		self._file_name_regex = re.compile(r'^iscp_perf_.*_.*.rpt$')
		self._command_name = ''
		self._unitIdRegex = re.compile("^(?P<unitId>.*?)_(?P<dateInFile>\d+?).rpt$")

	@property
	def line_format(self):
		return self._line_format

	def parse(self, file_path):
		counters_for_family = json.load(open('/opt/alticelabs/namf/src/shelf/collectorprocess/operators/Readers/TELCORDIA/COMMANDS/MODULES/mappingCounterforFamily.json'))
		logger.debug("Parsing TELCORDIA format, in file {0}".format(os.path.basename(file_path)))
		file_name = os.path.basename(file_path)

		#Get the unit from the filename
		data = self._unitIdRegex.match(file_name)
		unitId = data.group('unitId').upper()
		#set unitID obtained in filename
		if unitId not in counters_for_family.keys():
			return
		self._command_name = unitId

		# Open file for reading
		try:
			f = open(file_path, 'r')
			n_line = -1
			for line in reader(f,delimiter=';'):
				n_line += 1
				if not line or line == []:
					continue

				line[1] = '{:s} {:s}:00'.format(line[1].replace('/','-'), line[2])
				del line[2]
				if len(line) > len(counters_for_family[unitId]):
					logger.warning("Number of values in line {0} is different than number of announced columns in sample \"{1}\"".format(n_line, file_name), __file__)
					continue

				document = dict(zip(counters_for_family[unitId][:len(line)],line))
				if document['HOSTNAME'] == '':
					continue
                                document["GRANULARITYPERIOD"] = 1440
				try:
					try:
						data_time = FamilyObject.parseEnvelopeDataTime(document["RESULT_TIME"])
					except ValueError as e:
						logger.warning("Could not build mediationEnvelope due to {0}: ".format(e), __file__)
						continue
					yield {"dataTime": data_time, "granularitySec": document["GRANULARITYPERIOD"], "data": document}
				except Exception, e:
					logger.warning("Unable to process {0} in unit {1} because wrong format => {2}".format(file_name, unitId, e), __file__)
					continue
		except IOError:
			logger.error("ERROR[ISCP_PERF]: Could not open sample file {0} in read mode.".format(os.path.basename(file_path)))
