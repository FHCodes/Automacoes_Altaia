#!/usr/bin/env python

__doc__ = \
	'''
		NOKIA CORE MPLS XML files parser manager
	'''

__version__ = '1.0'

__authors__ = [
	"Version 1.0: Bruno Silva <bruno-e-silva@alticelabs.com>"
]

import xml.etree.cElementTree as ET
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



#from Operators.Readers.NSN.NSN_XML_SAM_STATS.MODULES import Command as BaseCommand

class Command(BaseCommand):

	def __init__(self):
		self._file_name_regex = re.compile(r"^.*.act0101.*")
		self._command_name = 'DBN0_MPLS_TRAFFIC_STATS'
		self._regex_to_FileName = re.compile("^(?P<NENAME>.*?).act0101.*")

	@property
	def line_format(self):
		return self._line_format

	def copy_catalog(self, catalog_Path):
		#Carregamos o ficheiro XML num objecto python e com a funcao iterparse permitenos aceder a cada uma das linhas do nosso ficheiro xml
		context= ET.iterparse(catalog_Path, events=("start", "end"))
		root = None
		#Tratamento dos dados do ficheiro
		#Vamos percorrer cada uma das linhas dos objectos python do ficheiro anteriormente de XML
		for event, elem in context:
			# #When the first element of all is parsed
			if event == "start" and root is None:
			# #This element becomes root to keep memory clean.
				root= elem
		return root


	def parse(self, file_path):
		logger.debug("[Reader] Reading Core MPLS XML file '{0}' contents...".format(os.path.basename(file_path)))

		file_name = os.path.basename(file_path)
		chassisField = (re.match(self._regex_to_FileName, file_name)).group('NENAME')

		try:
			root = (self.copy_catalog(file_path)).find('statsLog')
			tTimeField = int(root.find('time').get('t'))

			#Conversao da data que se encontra no formato epoch, implementado no reader de modo a agilisar o processamento do ficheiro, melhoria de 1080 por cento
			timeField= (datetime.datetime.fromtimestamp(tTimeField)).strftime('%Y-%m-%d %H:%M:%S')

			newDocument = dict()

			for tmp in root.findall('cmNio'):
				cmNio = tmp.find('data')
				fields = dict()
				fields['CHASSIS'] = chassisField.upper()
				fields['STARTTIME'] = timeField
				fields['TTIME'] = tTimeField
				fields['INTERVAL'] = 15
				fields['PORT'] = cmNio.get('port')
				cmNio.attrib.pop('port', None)
				fields['QID'] = cmNio.get('qId')
				cmNio.attrib.pop('qId', None)

				if 'LagPort' in cmNio.keys():
					fields['LAGPORT'] = cmNio.get('LagPort').title()
					fields['GROUP_TYPE'] = 'LAG'
					cmNio.attrib.pop('LagPort', None)
				else:
					fields['GROUP_TYPE'] = 'PORT'


				for attribute in cmNio.keys():
					fields['CMNIO_'+attribute.upper()] = cmNio.get(attribute)

				pk = fields['PORT'] +'_'+ fields['QID']

				if pk not in newDocument:
					newDocument[pk] = fields

			for tmp in root.findall('cmNeo'):
				cmNeo= tmp.find('data')
				fields = dict()

				pk = cmNeo.get('port') +'_'+ cmNeo.get('qId')
				for attribute in cmNeo.keys():
					if attribute not in ['LagPort','port','qId']:
						fields['CMNEO_'+attribute.upper()] = cmNeo.get(attribute)

				if pk not in newDocument:
					logger.warning('Pk not found: '+ pk)
				else:
					newDocument[pk].update(fields)

			for pk in newDocument.keys():
				try:
					data_time = FamilyObject.parseEnvelopeDataTime(newDocument[pk]["STARTTIME"])
				except ValueError as e:
					logger.warning("Could not build mediationEnvelope due to {0}: ".format(e), __file__)
					continue
				yield {"dataTime": data_time, "granularitySec": newDocument[pk]['INTERVAL'], "data": newDocument[pk]}
		except Exception as e:
			print e
			logger.warning("[warning] SAM STATS act0101 XML malformed: {0}".format(file_path))
