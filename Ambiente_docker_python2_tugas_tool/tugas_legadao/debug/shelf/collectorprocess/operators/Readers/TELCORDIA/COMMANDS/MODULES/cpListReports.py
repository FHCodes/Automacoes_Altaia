#!/usr/bin/env python

__version__ = '1.0'

__doc__ = '''

'''

__authors__ = [
	"Version 1.0: bruno-e-silva <bruno-e-silva@alticelabs.com>"
]

import os
import re
import copy
import importlib

# Local libraries
BaseOperator = importlib.import_module("shelf.collectorprocess.operators.BaseOperator").BaseOperator
FamilyObject = importlib.import_module("shelf.collectorprocess.operators.FamilyObject").FamilyObject
BaseCommand = importlib.import_module("shelf.collectorprocess.operators.Readers.TELCORDIA.COMMANDS.Operator").Command
logger = importlib.import_module("shelf.collectorprocess.logger").logger


# Command class that extends the base command defined in Operator.py
class Command(BaseCommand):

	def __init__(self):
		self._file_name_regex = re.compile(r'^cp_list\.reports\..*\.out$')
		self._command_name = 'CP_LIST.REPORTS'

	@property
	def line_format(self):
		return self._line_format

	def parse(self, file_path):
		logger.debug("Parsing BSC format, in file {0}".format(os.path.basename(file_path)))
		regexCounters = re.compile(r'^ (?P<counter>.+?)\s+=\s+(?P<value>.*?)$')
		regexNumber = re.compile(r'^Number of Data Pages Used \= (?P<Data_Pages_Used>.+?)\tData Pages Percent Free = (?P<Data_Pages_Free>.*?)$')
		file_name = os.path.basename(file_path)

		try:
			resulttime =  file_name.split('.')[3]
			resulttime = '{:s}-{:s}-{:s} 00:00:00'.format(resulttime[0:4], resulttime[4:6], resulttime[6:8])
		except:
			logger.error("ERROR[TELCORDIA_CPLISTREPORT]: Could not get date from fileName {0}.".format(os.path.basename(file_path)))
			return

		# Open file for reading
		try:
			f = open(file_path)
			lines = f.readlines()
			f.close()
			numberFlag = False
			startBlock = False
			while len(lines) > 0:
				line = lines.pop(0).strip('\n|\r')
				if line.startswith('-------------------------'):
					continue

				# Read file header
				if line.startswith('DataBase Usage for '):
					document = dict()
					document['HOSTNAME'] = line.split('DataBase Usage for ')[1].strip()
					if document['HOSTNAME'] != '':
						startBlock = True

				elif line.startswith('Number of Data Pages Used') and startBlock:
					data = regexNumber.match(line)
					document['DATA_PAGES_USED'] = data.group('Data_Pages_Used')
					document['DATA_PAGES_PERCENT_FREE'] = data.group('Data_Pages_Free')
					numberFlag = True

				elif numberFlag and startBlock and line.startswith(' Active Subs  '):
					data = regexCounters.match(line)
					while data != None and len(lines) > 0:
						counterId = data.group('counter').upper().replace('-','_').replace(' ', '_')
						if counterId in document.keys():
							counterId = 'AICE_' + counterId
						document[counterId] = data.group('value')
						line = lines.pop(0).strip('\n|\r')
						data = regexCounters.match(line)

					document['GRANULARITY_PERIOD'] = 1440
					document['RESULT_TIME'] = resulttime
					#print document
					#return
					try:
						# Parse the date
						data_time = FamilyObject.parseEnvelopeDataTime(document['RESULT_TIME'])
					except ValueError as e:
						logger.error("Could not build mediationEnvelope due to {0}: ".format(e), __file__)
						continue

					yield {"dataTime": data_time, "granularitySec": document['GRANULARITY_PERIOD'], "data": document}
					numberFlag = False
					startBlock = False

		except IOError:
			logger.error("ERROR[TELCORDIA_CPLISTREPORT]: Could not open sample file {0} in read mode.".format(os.path.basename(file_path)))
