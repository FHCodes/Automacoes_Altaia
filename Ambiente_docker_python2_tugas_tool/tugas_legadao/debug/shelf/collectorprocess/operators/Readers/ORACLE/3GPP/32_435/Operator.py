#!/usr/bin/env python

__doc__ = \
	'''
	Oracle 3GPP 32.435 Generic Performance XML reader

'''

__version__ = '1.0'

__authors__ = [
	"Version 1.0: Bruno Silva <bruno-e-silva@alticelabs.com>",
	"Version 2.0: Paulo Gil <paulo-a-gil@alticelabs.com>",
	"Version 2.1: Pedro Silva <pedro-c-silva@alticelabs.com>"

]

# Native libraries
import os
import re
import sys
import json
import copy
from datetime import datetime
import xml.etree.cElementTree as etree
import importlib
import gzip
import io

# Local libraries
BaseOperator = importlib.import_module("shelf.collectorprocess.operators.BaseOperator").BaseOperator
FamilyObject = importlib.import_module("shelf.collectorprocess.operators.FamilyObject").FamilyObject
logger = importlib.import_module("shelf.collectorprocess.logger").logger


def convertTimeZone(date):
	if '-' in date:
		d1 = datetime.strptime(date[:-6], '%Y-%m-%dT%H:%M:%S')
		d2 = datetime.strptime('0001-01-01 ' + date[-5:] + ':00', '%Y-%m-%d %H:%M:%S')
		t1 = datetime.strptime('0001-01-01 00:00:00', '%Y-%m-%d %H:%M:%S')
		return t1 + (d1 - d2)
	return datetime.strptime(date, '%Y-%m-%dT%H:%M:%S')


class Operator(BaseOperator):

	# Class Constructor
	def __init__(self, operationParams, baseObject={}):
		BaseOperator.__init__(self, operationParams, baseObject=baseObject)

		self.datetime_regex = re.compile(r'^(?P<datetime>\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}).*$')

		# Sets the interval unit, as default its defined to Minutes
		self.intervalUnit = 'S'
		if "intervalUnit" in self.options:
			self.intervalUnit = self.options["intervalUnit"].upper()

		# Sets the interval unit, as default its defined to Minutes
		self._convertTimeZone = True
		if "convertTimeZone" in self.options:
			self._convertTimeZone = (False if self.options["convertTimeZone"].upper() == 'FALSE' else True)

		if "config" not in self.options:
			logger.warning('Missing flag "config" in spec, using generic configuration!')
			self.options["config"] = "generic"

		self._config = json.load(
				open(os.path.join(os.path.dirname(__file__), "config", '{0}.json'.format(self.options["config"]))))
		self._regex = re.compile(self._config['regex'])

		self._default_family = ''
		if "default_family" in self.options:
			self._default_family = self.options["default_family"].upper()
		elif 'default_family' in self._config.keys():
			self._default_family = self._config["default_family"].upper()

	def process(self, familyObj=FamilyObject(), baseObject={}):

		filesToBeProcessed = familyObj.getFiles()
		familyObj.clearFiles()

		for filePath in filesToBeProcessed:

			fileName = os.path.basename(filePath)
			familyObj.fileName = fileName

			if os.path.getsize(filePath) == 0:
				logger.warning("File {0} is empty.".format(fileName), __file__)
				continue

			try:
				# If file is compressed, replace the file path with a gzip buffered stream
				if os.path.splitext(fileName)[1] == ".gz":
					filePath = io.BufferedReader(gzip.open(filePath))
				# Sligthly less efficient alternative for large files, but slightly faster for smaller files.
				# Keep this in comment, if case circumstances change
				# p = subprocess.Popen(["zcat", filePath], stdout=subprocess.PIPE)
				# filePath = cStringIO.StringIO(p.communicate()[0])
			except IOError:
				logger.warning("Could not open sample file \"{}\" in read mode: ".format(fileName), __file__)
				continue
			self.measInfoId = ''

			logger.debug(
				"[Reader] Reading Oracle Performance 3GPP 32.435 XML files '{0}' contents...".format(fileName),
				__file__)

			self.fast_iter(filePath, familyObj, baseObject)

	def fast_iter(self, filePath, familyObj, baseObject):
		context = iter(etree.iterparse(filePath, events=('start', 'end')))
		# get root element
		_, root = next(context)

		config = self._config

		tag = list()

		for elem in config:
			if elem != 'regex':
				try:
					for t in config[elem]['tags']:
						tag.append(t)
						for attr in config[elem]['tags'][t]['attrs']:
							tag.append(attr)
				except:
					pass

		if isinstance(tag, list):
			multi = True
		else:
			multi = False

		fixedDoc = dict()
		firstMeasData = True
		sharedDoc = dict()
		document = dict()
		counters = dict()
		namespace = None

		for event, elem in context:
			if event == 'start' and namespace is None:
				if "}" in elem.tag:
					namespace = elem.tag.split("}")[0].strip("{")
					namespace = "{" + namespace + "}"
				else:
					namespace = ""

			elem.tag = elem.tag.replace(namespace, '')

			if multi:
				if event == 'start':

					if elem.tag == 'measData':
						if firstMeasData:
							fixedDoc = copy.deepcopy(sharedDoc)
							firstMeasData = False
						sharedDoc.clear()
						sharedDoc.update(fixedDoc)
						self.measInfoId = ""
						continue

					if elem.tag == 'measType':
						index = elem.get('p')
						continue

					elif elem.tag == 'r':
						index = elem.get('p')
						continue

					elif elem.tag == 'measInfo':
						if 'measInfoId' in tag:
							self.measInfoId = elem.get('measInfoId').upper()
						counters = dict()
						elem.clear()
						continue

					elif elem.tag == 'measValue':
						document = copy.deepcopy(sharedDoc)
						if 'measValue' in tag:
							document['MEASOBJLDN'] = elem.get('measObjLdn')
						elem.clear()
						continue

					for key in elem.attrib.keys():
						if key in tag:

							header = config['header']['tags']

							try:
								objects = config['object']['tags']
							except:
								objects = []
								pass

							if elem.tag in objects:
								if key in objects[elem.tag]['attrs']:
									for obj in objects[elem.tag]['attrs'][key]:
										if obj not in document:
											document[obj] = elem.get(key)

							elif elem.tag in header:
								if key in header[elem.tag]['attrs']:
									counters = dict()
									for obj in header[elem.tag]['attrs'][key]:
										if obj not in sharedDoc:
											sharedDoc[obj] = elem.get(key)

							if key == 'duration' and 'DURATION' in sharedDoc.keys():
								sharedDoc['DURATION'] = self.format_interval(
									int(FamilyObject.parseEnvelopeGranularitySec(elem.get('duration'))),
									elem.get('duration')[-1:], self.intervalUnit)

							elif key == 'beginTime' and 'BEGINTIME' in sharedDoc.keys():
								if self._convertTimeZone:
									sharedDoc['BEGINTIME'] = datetime.strftime(convertTimeZone(sharedDoc['BEGINTIME']),
																			   '%Y-%m-%d %H:%M:%S')
								else:
									sharedDoc['BEGINTIME'] = sharedDoc['BEGINTIME'][0:19].replace('T', ' ')
							elif key == 'endTime' and 'ENDTIME' in sharedDoc.keys():
								if self._convertTimeZone:
									sharedDoc['ENDTIME'] = datetime.strftime(convertTimeZone(sharedDoc['ENDTIME']),
																			 '%Y-%m-%d %H:%M:%S')
								else:
									sharedDoc['ENDTIME'] = sharedDoc['ENDTIME'][0:19].replace('T', ' ')

				elif event == 'end':

					if elem.tag == 'measType':
						counters[index] = elem.text.upper()

					elif elem.tag == 'r':
						document[counters[index]] = elem.text

					elif elem.tag == 'measValue':
						if self.measInfoId == '':
							try:
								self.measInfoId = document['MEASINFOID']
							except KeyError:
								if self._default_family:
									self.measInfoId = self._default_family
								else:
									self.measInfoId = ''

						if self.measInfoId != '':
							measObj = familyObj.fileName
							document['MEASUREMENTDATAOBJECT'] = measObj.replace('.xml', '').replace('.gz', '')
							value = re.sub(self._regex, '', self.measInfoId)

							if value != '':
								self.measInfoId = value

							familyObj.setUnitID(self.measInfoId)

							familyObj.clearDocuments()

							try:
								data_time = FamilyObject.parseEnvelopeDataTime(document['BEGINTIME'])
							except ValueError as e:
								logger.warning("Could not build mediationEnvelope due to : {0}".format(e), __file__)
								continue

							data_document = {"dataTime": data_time,
											 "granularitySec": self.format_interval(document['DURATION'],
																					self.intervalUnit, 'S'),
											 "data": document}
							familyObj.addDocument(data_document)
							self.nextOp(familyObj=familyObj, baseObject=baseObject)

					elem.clear()
			else:
				elem.clear()

		del context

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
