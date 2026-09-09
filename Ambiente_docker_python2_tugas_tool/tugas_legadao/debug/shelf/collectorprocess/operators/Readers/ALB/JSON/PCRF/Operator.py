#!/usr/bin/env python

__doc__ = \
	'''
	PCRF Performance JSON reader
	'''

__version__ = '1.0'

__authors__ = [
	"Version 0.1: Gil Martins <gil-l-martins@alticelabs.com>"
]

import re
from csv import reader
import os
import importlib
from datetime import datetime, timedelta
import json

# Local libraries
BaseOperator = importlib.import_module("shelf.collectorprocess.operators.BaseOperator").BaseOperator
FamilyObject = importlib.import_module("shelf.collectorprocess.operators.FamilyObject").FamilyObject
logger = importlib.import_module("shelf.collectorprocess.logger").logger


class Operator(BaseOperator):

	# Class Constructor
	def __init__(self, operationParams, baseObject={}):
		BaseOperator.__init__(self, operationParams, baseObject=baseObject)

	####################################################################################################################

	@staticmethod
	def convert_timezone(date):
		if '-' in date or '+' in date:
			d1 = datetime.strptime(date[:-6], '%Y-%m-%dT%H:%M:%S.%f')
			d2 = datetime.strptime('0001-01-01 ' + date[-5:] + ':00', '%Y-%m-%d %H:%M:%S')
			t1 = datetime.strptime('0001-01-01 00:00:00', '%Y-%m-%d %H:%M:%S')
			return t1 + (d1 - d2)
		return datetime.strptime(date, '%Y-%m-%dT%H:%M:%S')

	@staticmethod
	def set_starttime(date):
		date = datetime.strptime(date[:-6], "%Y-%m-%dT%H:%M:%S.%f")
		return datetime.strftime(date, "%Y-%m-%d %H:%M:%S")

	@staticmethod
	def add_standard_unit(doc, counter, key, value):
		key = key.replace('[', '_')
		counter_id = '_'.join([counter, key])
		doc[counter_id] = value

	def standard_procedure(self, doc, counter, values):
		try:
			props = values['props']
			for entry, value in props.items():
				entry = entry.replace(']', '').upper()
				self.add_standard_unit(doc, counter, entry, value)
		except KeyError:
			return  # no values to unpack

	def subunits_procedure(self, doc, sub_doc, sub_id, counter, values, subfield, counter_div=None, pref=None):
		try:
			props = values['props']

			if subfield == 'PARTITION_NAME':
				subkey = '_'.join(counter_div[1:])
				for entry, value in props.items():
					entry = entry.replace(']', '').upper()
					entry_div = entry.split('[')
					if len(entry_div) > 1:
						if subkey not in sub_doc[sub_id]:
							sub_doc[sub_id][subkey] = {}
							sub_doc[sub_id][subkey][subfield] = subkey
						c_id = '_'.join([pref, entry_div[-1]])
						sub_doc[sub_id][subkey][c_id.upper()] = value
					else:
						self.add_standard_unit(doc, counter, entry, value)

			elif subfield == 'IF_NAME':
				subkey = counter_div[-1]
				for entry, value in props.items():
					entry = entry.replace(']', '').upper()
					entry_div = entry.split('[')
					if len(entry_div) > 1:
						if subkey not in sub_doc[sub_id]:
							sub_doc[sub_id][subkey] = {}
							sub_doc[sub_id][subkey][subfield] = subkey
						c_id = '_'.join([pref, counter_div[1], entry_div[-1]])
						sub_doc[sub_id][subkey][c_id.upper()] = value
					else:
						self.add_standard_unit(doc, counter, entry, value)

			elif subfield == 'RESULT_CODE':
				for entry, value in props.items():
					entry = entry.replace(']', '')
					entry_div = entry.split('[')
					subkey = entry_div[-1]
					if len(entry_div) > 1:  # and entry_div[0] in ['RESULTS', 'RESULTS_PCT']:
						if subkey not in sub_doc[sub_id]:
							sub_doc[sub_id][subkey] = {}
							sub_doc[sub_id][subkey][subfield] = subkey
						sub_doc[sub_id][subkey][entry_div[0].upper()] = value
					else:
						self.add_standard_unit(doc, counter, entry.upper(), value)

		except KeyError:
			return  # no values to unpack

	####################################################################################################################

	def process(self, familyObj=FamilyObject(), baseObject={}):
		files_to_process = familyObj.getFiles()
		logger.debug("Reading PCRF Performance JSON files' contents...", __file__)
		familyObj.clearDocuments()

		for filePath in files_to_process:

			file_name = os.path.basename(filePath)
			familyObj.fileName = file_name

			try:
				# Open file for writing
				f = open(filePath, 'r')
			except IOError:
				logger.error(
					"Could not open sample file \"{0}\" in read mode: ".format(file_name), __file__)
				continue

			# load json data
			data = json.load(f)

			try:
				unit_id = data['app'].replace('-', '_').upper()
				familyObj.setUnitID(unit_id)
			except (KeyError, TypeError):
				logger.warning("No unit id found in file \"{0}\"".format(file_name), __file__)
				continue

			try:
				base_document = {
					'GRANULARITYPERIOD': 1,
					'HOST': data['host'],
					'INSTANCE': data['inst']
				}

				date_string = next((value['date'] for value in data['kpis'].values() if 'date' in value), None)
				if date_string is None:
					logger.warning("Start time was not possible to fetch from file \"{0}\"".format(file_name), __file__)
					continue

				base_document['STARTTIME'] = self.set_starttime(date_string)

			except KeyError:
				logger.warning("No host, instance or kpis in file \"{0}\"".format(file_name), __file__)
				continue

			document = {}
			subunit_document = {}

			dsgw_submatch = [
				'DSGW_RTDAPREPORT_RTDAP_RX_MSG_COUNTER',
				'DSGW_RTDAPREPORT_RTDAP_TX_MSG_COUNTER',
				'DSGW_RTDAPREPORT_RTDAP_ERROR',
				'DSGW_RTDAPREPORT_RTDAP_GENERIC_ERROR',
				'IDS_RESULT_CODE',
				'IDS_RECEIVED_RESULT_CODE'
			]

			oms_daemon_submatch = {
				'INODE': 'PARTITION_NAME',
				'FS': 'PARTITION_NAME',
				'IF': 'IF_NAME'
			}

			if unit_id == 'DSCP_DSGW':
				for counter, values in data['kpis'].items():
					counter = counter.upper()

					if counter in dsgw_submatch:
						# set id of subunit
						subunit_id = '_'.join([unit_id, counter])
						if subunit_id not in subunit_document:
							subunit_document[subunit_id] = {}
						self.subunits_procedure(document, subunit_document, subunit_id, counter, values, 'RESULT_CODE', None, None)
					else:
						self.standard_procedure(document, counter, values)

			elif unit_id == 'OMS_DAEMON':
				for counter, values in data['kpis'].items():
					counter_div = counter.split('_')
					pref = counter_div[0]
					counter = counter.upper()

					if pref in oms_daemon_submatch:
						# set id of subunit
						subunit_id = '_'.join([unit_id, pref])
						if subunit_id not in subunit_document:
							subunit_document[subunit_id] = {}
						self.subunits_procedure(document, subunit_document, subunit_id, counter, values, oms_daemon_submatch[pref], counter_div, pref)
					else:
						self.standard_procedure(document, counter, values)

			else:
				# standard procedure for every other family
				for counter, values in data['kpis'].items():
					counter = counter.upper()
					self.standard_procedure(document, counter, values)

			data.clear()

			# BUILD ENVELOPES ##########################################################################################
			try:
				data_time = familyObj.parseEnvelopeDataTime(base_document["STARTTIME"])  # TBD
				granularity_sec = familyObj.parseEnvelopeGranularitySec(
					self.format_interval(base_document["GRANULARITYPERIOD"], 'M', 'S'))  # TBD
			except ValueError as e:
				logger.warning("Could not build mediationEnvelope due to {0}: ".format(e), __file__)
				continue

			# send unit envelope
			document.update(base_document)
			try:
				familyObj.addDocument({"dataTime": data_time, "granularitySec": granularity_sec, "data": document})
				self.nextOp(familyObj=familyObj, baseObject=baseObject)
				familyObj.clearDocuments()
			except Exception, e:
				logger.warning(
					"Unable to process {0} in unit {1} because wrong format => {2}".format(familyObj.fileName, unit_id, e), __file__)
				continue

			document.clear()

			# send subunit envelopes
			for subunit_id in subunit_document:
				for subkey in subunit_document[subunit_id]:
					try:
						subunit_document[subunit_id][subkey].update(base_document)
						familyObj.setUnitID(subunit_id)
						familyObj.addDocument({"dataTime": data_time, "granularitySec": granularity_sec, "data": subunit_document[subunit_id][subkey]})
						self.nextOp(familyObj=familyObj, baseObject=baseObject)
						familyObj.clearDocuments()
					except Exception, e:
						logger.warning(
							"Unable to process {0} in unit {1} because wrong format => {2}".format(familyObj.fileName, unit_id, e), __file__)
						continue

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
