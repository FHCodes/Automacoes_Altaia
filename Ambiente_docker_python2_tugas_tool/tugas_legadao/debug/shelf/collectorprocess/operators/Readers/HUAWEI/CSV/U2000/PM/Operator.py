#!/usr/bin/env python

__doc__ = \
	'''
	Huawei U2000 Performance CSV reader
'''

__version__ = '1.2'

__authors__ = [
	"Version 0.1: Francisco Santiago <francisco-j-santiago@telecom.pt>"
	"Version 1.1: Joao Pio <joao-t-pio@telecom.pt>"
	"Version 1.2: Bruno Silva <bruno-e-silva@alticelabs.com>"
]

import re
from csv import reader
import os
import importlib
from datetime import datetime, timedelta

# Local libraries
BaseOperator = importlib.import_module("shelf.collectorprocess.operators.BaseOperator").BaseOperator
FamilyObject = importlib.import_module("shelf.collectorprocess.operators.FamilyObject").FamilyObject
logger = importlib.import_module("shelf.collectorprocess.logger").logger


class Operator(BaseOperator):

	# Class Constructor
	def __init__(self, operationParams, baseObject={}):
		BaseOperator.__init__(self, operationParams, baseObject=baseObject)

		self.filter_reliability = False
		try:
			if 'filter_reliability' in self.options and self.options['filter_reliability'] == "True":
				self.filter_reliability = True
		except Exception:
			# if any exception is thrown, something might be wrong and we want to keep original behaviour.
			pass


	def process(self, familyObj=FamilyObject(), baseObject={}):

		files_to_process = familyObj.getFiles()
		regex_to_FileName = re.compile("^(.*)pmresult_(?P<UnitID>.+?)_\w+_.*.csv$")
		logger.debug("Reading Huawei Performance CSV files' contents...", __file__)
		for filePath in files_to_process:

			familyObj.clearDocuments()

			# Get file's name to find the unitID
			file_name = os.path.basename(filePath)
			regex_match_fileName=regex_to_FileName.match(file_name)
			if regex_match_fileName != None:
				unit_id=regex_match_fileName.group('UnitID')
				#print unit_id
			else:
				logger.warning("Could not obtain unit ID from sample name ".format(regex_match_fileName, file_name))
				continue

			familyObj.setUnitID(unit_id)

			familyObj.fileName = file_name
			try:
				# Open file for writing
				f = open(filePath, 'r')
			except IOError:
				logger.error(
					"Could not open sample file \"{0}\" in read mode: ".format(file_name), __file__)
				continue

			# Used to store the column names from the first line of each file
			column_names_list = None
			n_column_names = 0
			# Used to enforce the 'reliability' filter depending on starting config and header of file
			apply_reliability_filter = False
			discarded_lines = 0

			n_line = 0
			for line in reader(f):

				familyObj.clearDocuments()

				n_line += 1

				# Collects column names from first line of file
				if n_line == 1:
					if len(line) == 0:
						logger.warning(
							"No column names found in first line of file \"{0}\"".format(file_name), __file__)
						break

					column_names_list = [x.upper() for x in line]
					n_column_names = len(column_names_list)

					# Check if 'Reliability' field exists in header. If not, no filter will be applied.
					if self.filter_reliability and 'RELIABILITY' in column_names_list:
						apply_reliability_filter = True
					continue

				# Skips second line that has no content
				if n_line == 2:
					continue

				# Checks if number of values in row is the same as the announced columns in the first line
				if len(line) != n_column_names:
					logger.warning(
						"Number of values in line {0} is different than number of announced columns in sample \"{1}\"".format(n_line, file_name), __file__)
					continue

				document = dict(zip(column_names_list, line))

				try:
					if apply_reliability_filter and str(document['RELIABILITY']).upper() != 'RELIABLE':
						# discard data
						discarded_lines += 1
						continue
				except KeyError:
					# safe measure: should never arrive here, since 'Reliability' check was done prior.
					pass

				try:
					try:
						data_time = familyObj.parseEnvelopeDataTime(document["RESULT TIME"])
						granularity_sec = familyObj.parseEnvelopeGranularitySec(self.format_interval(int(document["GRANULARITY PERIOD"]), 'M', 'S'))
					except ValueError as e:
						logger.warning("Could not build mediationEnvelope due to {0}: ".format(e), __file__)
						continue

					try:
						# Result time comes with the format YYYY-MM-DD HH:mm The preferred format is YYYY-MM-DD HH:mm:ss
						document["RESULT TIME"] += ":00"
						# End Time is obtained by converting Result Time to datetime object + granularity, and back to string object
						document["END TIME"] = (datetime.strptime(document["RESULT TIME"], '%Y-%m-%d %H:%M:%S') + timedelta(minutes=int(document["GRANULARITY PERIOD"]))).strftime('%Y-%m-%d %H:%M:%S')

					except Exception, e:
						logger.warning("Could not convert RESULT TIME due to '{0}'".format(e), __file__)

					familyObj.addDocument({"dataTime": data_time, "granularitySec": granularity_sec, "data": document})

					# Final operations to the fields with timestamp and granularity period

					self.nextOp(familyObj=familyObj, baseObject=baseObject)
				except Exception, e:
					logger.warning("Unable to process {0} in unit {1} because wrong format => {2}".format(familyObj.fileName, unit_id, e), __file__)
					continue

			if apply_reliability_filter and discarded_lines > 0:
				logger.info('Reliability filter: {0} event(s) discarded due to not being Reliable.'.format(str(discarded_lines)))


	@staticmethod
	def format_interval(value, base_format, unit_format):

		matrix_data = {
			'S':
			{
				'S':
				{
					'value': 1,
					'operation': ''
				},
				'M':
				{
					'value': 60,
					'operation': '/'
				},
				'H':
				{
					'value': 3600,
					'operation': '/'
				}
			},
			'M':
			{
				'S':
				{
					'value': 60,
					'operation': '*'
				},
				'M':
				{
					'value': 1,
					'operation': ''
				},
				'H':
				{
					'value': 60,
					'operation': '/'
				}
			},
			'H':
			{
				'S':
				{
					'value': 3600,
					'operation': '*'
				},
				'M':
				{
					'value': 60,
					'operation': '*'
				},
				'H':
				{
					'value': 1,
					'operation': ''
				}
			}
		}

		if matrix_data[base_format][unit_format]['operation'] == '*':
			return value * matrix_data[base_format][unit_format]['value']
		elif matrix_data[base_format][unit_format]['operation'] == '/':
			return value / matrix_data[base_format][unit_format]['value']
		return value
