#!/usr/bin/env python

__doc__ = \
	'''
		NOKIA CORE MPLS XML files parser manager
	'''

__version__ = '1.0'

__authors__ = [
	"Version 1.0: Bruno Silva <bruno-e-silva@alticelabs.com>"
]

import xml.etree.cElementTree as etree
import datetime
import os
import pkgutil
import time
import re
import importlib


# Local libraries
BaseOperator = importlib.import_module("shelf.collectorprocess.operators.BaseOperator").BaseOperator
FamilyObject = importlib.import_module("shelf.collectorprocess.operators.FamilyObject").FamilyObject
BaseCommand = importlib.import_module("shelf.collectorprocess.operators.Readers.NOKIA.XML_SAM_STATS.Operator").Command
logger = importlib.import_module("shelf.collectorprocess.logger").logger

#from Operators.Readers.NSN.NSN_XML_SAM_STATS.Operator import Command as BaseCommand

class Command(BaseCommand):

	def __init__(self):
		self._file_name_regex = re.compile(r"^.*.act0202.*")
		self._command_name = ''
		self._regex_to_FileName = re.compile("^(?P<NENAME>.*?).act0202.*")

	@property
	def line_format(self):
		return self._line_format

	def getLineData(self, line):
		document = dict()
		groupsData = re.findall(self._getData, line)
		for key, value in groupsData:
			document[key.upper()] = value
		return document

	def parse(self, file_path):
		logger.debug("Parsing ERICSSON command , in file {0}".format(os.path.basename(file_path)))

		file_name = os.path.basename(file_path)

		#try:
		NENAME = (re.match(self._regex_to_FileName, file_name)).group('NENAME')
		#except Exception as ex:
		#   logger.warning("It was not possible to obtain NENAME information in command {0} from file {1}".format(self._command_name, file_name))

		try:
			context = iter(etree.iterparse(file_path, events=('start', 'end')))
			# get root element
			_, root = next(context)

			tag = ['time', 'cpSipo', 'cpSepo', 'data']

			if isinstance(tag, list):
				multi = True
			else:
				multi = False

			refType = ''
			namespace = None
			for event, elem in context:
				if event == 'start' and namespace is None:
					if "}" in elem.tag:
						namespace = elem.tag.split("}")[0].strip("{")
						namespace = "{" + namespace + "}"
					else:
						namespace = ""

				if multi:
					if event == 'start':
						if elem.tag == namespace + 'time':
							#Conversao da data que se encontra no formato epoch, implementado no reader de modo a agilisar o processamento do ficheiro, melhoria de 1080 por cento
							t = int(elem.get('t'))
							timeField= (datetime.datetime.fromtimestamp(t)).strftime('%Y-%m-%d %H:%M:%S')
							elem.clear()

						elif elem.tag == namespace + 'cpSipo':
							refType = 'CPSIPO'
							elem.clear()

						elif elem.tag == namespace + 'cpSepo':
							refType = 'CPSEPO'
							elem.clear()

						elif elem.tag == namespace + 'data':
							document = dict()
							document['TTIME'] = t
							document['STARTTIME'] = timeField
							document['INTERVAL'] = 15
							document['NENAME'] = NENAME.upper()
							document['PORT'] = "N/A"
							for attr in elem.attrib.keys():
								document[attr.upper()] = elem.get(attr)

							if 'PID' in document.keys():
								self._command_name = 'DBN0_MPLS_SAP_INGRESS_POLICER_STATS'
							elif 'QID' in document.keys():
								if refType == 'CPSIPO':
									self._command_name = 'DBN0_MPLS_SAP_INGRESS_QUEUE_STATS'
								elif refType == 'CPSEPO':
									self._command_name = 'DBN0_MPLS_SAP_EGRESS_QUEUE_STATS'
								else:
									continue
							else:
								continue
							refType = ''
							try:
								data_time = FamilyObject.parseEnvelopeDataTime(document["STARTTIME"])
							except ValueError as e:
								logger.warning("Could not build mediationEnvelope due to {0}: ".format(e), __file__)
								continue
							yield {"dataTime": data_time, "granularitySec": document['INTERVAL'], "data": document}
							elem.clear()

					elif event == 'end':
						elem.clear()
				else:
					elem.clear()
			del context

		except Exception as ex:
			logger.warning(ex)
			logger.warning("It was not possible to obtain MPLS information in command {0} from file {1}".format(self._command_name, file_name))
