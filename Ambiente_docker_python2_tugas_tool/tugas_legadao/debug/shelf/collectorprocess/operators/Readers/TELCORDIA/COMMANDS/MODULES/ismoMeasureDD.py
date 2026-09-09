#!/usr/bin/env python

__version__ = '1.0'

__doc__ = '''

'''

__authors__ = [
	"Version 1.0: bruno-e-silva <bruno-e-silva@alticelabs.com>"
]

from datetime import date, timedelta
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

				# Read file header
				if hostname == '':
					data = regexHostName.match(line)
					try:
						if data.group('hostname') != None:
							hostname = hostname.group('hostname')
					except:
						continue

				elif line.startswith('________') and hostname != '':
					while line != '':
						line = lines.pop(0).strip('\n|\r')
						document = dict()
						document['HOSTNAME'] = hostname
						if '24' in document['RESULT_TIME']:
							t = time.strptime(resultTime, "%d-%m-%Y")
							newDate = date(t.tm_year,t.tm_mon,t.tm_mday) + timedelta(1)
							document['RESULT_TIME'] = '{:s} {:s}:00'.format(newDate.strftime('%d-%m-%Y'), document['RESULT_TIME'].replace('24', '00'))

						else:
							document['RESULT_TIME'] = '{:s} {:s}:00'.format(resulttime, document['RESULT_TIME'])
						document['GRANULARITY_PERIOD'] = 1440
						document["Intact_Billing_Rec_Received"] = values[1]
						document["Error_Billing_Rec_Received"] = values[2]
						document["Billing_Rec_Generated"] = values[3]
						document["DRS_Rec_Received"] = values[4]
						document["Intact_ASCII_Samp_Rec_Received"] = values[5]
						document["Error_ASCII_Samp_Rec_Received"] = values[6]
						document["Total_Rec_Received"] = values[7]

						try:
							# Parse the date
							data_time = FamilyObject.parseEnvelopeDataTime(document['RESULT_TIME'])
						except ValueError as e:
							logger.error("Could not build mediationEnvelope due to {0}: ".format(e), __file__)
							continue

						yield {"dataTime": data_time, "granularitySec": document['GRANULARITY_PERIOD'], "data": document}

					hostname = ''

		except IOError:
			logger.error("ERROR[TELCORDIA_CPLISTREPORT]: Could not open sample file {0} in read mode.".format(os.path.basename(file_path)))
