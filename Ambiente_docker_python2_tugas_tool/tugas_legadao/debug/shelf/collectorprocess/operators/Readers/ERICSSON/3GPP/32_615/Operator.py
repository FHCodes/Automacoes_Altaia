#!/usr/bin/env python

__doc__ = \
	'''
	Ericsson Parameters 3GPP 32.615 XML reader

'''

__version__ = '1.0'

__authors__ = [
				"Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>"
                "Version 1.1: Rafael Gomes <rafael-g-gomes@alticelabs.com>"
			]

# Native libraries
import xml.etree.cElementTree as etree
import os, sys, json
from datetime import timedelta, datetime
import re
import importlib
import copy

# Local libraries
BaseOperator = importlib.import_module("shelf.collectorprocess.operators.BaseOperator").BaseOperator
FamilyObject = importlib.import_module("shelf.collectorprocess.operators.FamilyObject").FamilyObject
logger = importlib.import_module("shelf.collectorprocess.logger").logger


class Operator(BaseOperator):

	# Class Constructor
	def __init__(self, operationParams, baseObject={}):
		BaseOperator.__init__(self, operationParams, baseObject=baseObject)

		# Initialize consolidation flag according to spec file
		self.consolidation = False
		if "consolidation" in self.options:
			if self.options["consolidation"].upper() == "TRUE":
				self.consolidation = True

		# Initialize config location according to spec file


		self.configDir = ''
		if "configDir" in self.options:
			self.configDir = self.options["configDir"]

		# 3G
		self.utranCellList = list()
		# 2G
		self.geranCellList = list()
		self.tech=''

		if "tech" in self.options:
			self.tech = self.options["tech"]



	def process(self, familyObj=FamilyObject(), baseObject={}):

		filesToBeProcessed = familyObj.getFiles()
		familyObj.clearFiles()

		for filePath in filesToBeProcessed:

			fileName = os.path.basename(filePath)
			familyObj.fileName = fileName
			self.timeCache = dict()
			self.measInfoId = ''

			logger.debug("[Reader] Reading Ericsson Parameters 3GPP 32.615 XML files '{0}' contents...".format(fileName), __file__)

			# Verifica se o ficheiro esta vazio
			if os.path.getsize(filePath) == 0:
				logger.warning("File {0} is empty.".format(fileName), __file__)
				continue

			self.fast_iter(filePath, familyObj, baseObject, self.header_iter(filePath))

	def header_iter(self, filePath):
		context = iter(etree.iterparse(filePath, events=('start', 'end')))
		# get root element
		_, root = next(context)

		sharedDoc = dict()
		sharedDoc['GRANULARITYPERIOD'] = 1440
		readAttributes = False
		containerId = ''

		for event, elem in context:
			try:
				if '}' in elem.tag:
					elem.tag = elem.tag.split('}')[1]
				else:
					elem.tag = elem.tag
			except Exception as e:
				print e
			if event == 'start':
				if elem.tag == 'fileHeader':
					sharedDoc['FILEFORMATVERSION'] = elem.get('fileFormatVersion')
					sharedDoc['VENDORNAME'] = elem.get('vendorName')
				elif elem.tag == 'fileFooter':
					if '.' in elem.get('dateTime'):
						sharedDoc['DATETIME'] = (elem.get('dateTime').split('.'))[0]
					else:
						sharedDoc['DATETIME'] = (elem.get('dateTime')[:-1] if elem.get('dateTime').endswith('Z') else elem.get('dateTime'))
				elif elem.tag == 'VsDataContainer':
					containerId = elem.get('id')
				elif elem.tag == 'vsDataUtranCell':
					self.utranCellList.append(containerId)
				elif elem.tag == 'vsDataGeranCell':
					self.geranCellList.append(containerId)
			elem.clear()
		del context
		return sharedDoc

	def fast_iter(self, filePath, familyObj, baseObject, sharedDoc):

		if self.tech=='2G':
			if self.configDir != '':
				try:
					fileInfo = re.match(r'^.*SubNetwork=(?P<BSC_NAME>[^,.]+?),MeContext=(?P<BTS_NAME>[^,.]+?).xml.*$', filePath)
					caracterization = json.load(open('{0}config_{1}.json'.format(self.configDir, baseObject.args.sourceId)))
					if fileInfo.group('BTS_NAME') in caracterization.keys():
						sharedDoc['BTS_NAME'] = fileInfo.group('BTS_NAME')
						sharedDoc['BSC_NAME'] = caracterization[fileInfo.group('BTS_NAME')]['BSC_NAME']
					else:
						for key in caracterization.keys():
							if fileInfo.group('BSC_NAME') == caracterization[key]['BSC_NAME']:
								sharedDoc['BSC_NAME'] = caracterization[key]['BSC_NAME']
							elif fileInfo.group('BTS_NAME') == caracterization[key]['BSC_NAME']:
								sharedDoc['BSC_NAME'] = caracterization[key]['BSC_NAME']
				except Exception as e:
					print e

			if 'BSC_NAME' not in sharedDoc:
				self.configDir = ''
		else:
			if self.configDir != '':
				try:
					fileInfo = re.match(r'^.*SubNetwork=(?P<RNC_NAME>[^,.]+?),MeContext=(?P<NODEB_NAME>[^,.]+?).xml.*$', filePath)
					caracterization = json.load(open('{0}config_{1}.json'.format(self.configDir, baseObject.args.sourceId)))
					if fileInfo.group('NODEB_NAME') in caracterization.keys():
						sharedDoc['NODEB_NAME'] = fileInfo.group('NODEB_NAME')
						sharedDoc['RNC_NAME'] = caracterization[fileInfo.group('NODEB_NAME')]['RNC_NAME']
					else:
						for key in caracterization.keys():
							if fileInfo.group('RNC_NAME') == caracterization[key]['RNC_NAME']:
								sharedDoc['RNC_NAME'] = caracterization[key]['RNC_NAME']
							elif fileInfo.group('NODEB_NAME') == caracterization[key]['RNC_NAME']:
								sharedDoc['RNC_NAME'] = caracterization[key]['RNC_NAME']
				except Exception as e:
					print e

			if 'RNC_NAME' not in sharedDoc:
				self.configDir = ''

		context = iter(etree.iterparse(filePath, events=('start', 'end')))
		# get root element
		_, root = next(context)

		readAttributes = False
		objectFILO = list()

		inContainer = False
		inAttributes = False
		popList = list()
		newDocument = dict()
		subCounter = dict()
		elements = list()
		elementAtributes = dict()
		containerId = None
		counter = None
		readToDocument = False

		inMemory = None
		enrichDict = dict()

		for event, elem in context:
			try:
				if '}' in elem.tag:
					elem.tag = elem.tag.split('}')[1]
			except Exception as e:
				print e

			if event == 'start':
				if 'id' in elem.attrib:
					containerId = elem.get('id')

				if elem.tag == 'configData':
					# Objects data inside
					sharedDoc['DNPREFIX'] = elem.get('dnPrefix')

				elif elem.tag == 'VsDataContainer':
					# gets id from container for hierarchy
					containerId = elem.get('id')
					inContainer = True

				elif elem.tag == 'vsDataType':
					value = elem.text

				elif elem.tag == 'attributes':
					#limpar e preparar para informacao de objecto
					inAttributes = True
					#readAttributes = True

				elif readToDocument:
					if elem.getchildren() != []:
						inMemory = copy.deepcopy(newDocument)
						newDocument = copy.deepcopy(sharedDoc)
						newDocument['DATATYPE'] = elem.tag
						if newDocument['DATATYPE'] not in subCounter.keys():
							subCounter[newDocument['DATATYPE']] = 1
						else:
							subCounter[newDocument['DATATYPE']] += 1
						newDocument['FDN'] = '{0},{1}={2}'.format(objectFILO[-1], elem.tag, subCounter[newDocument['DATATYPE']])
					else:
						counter = elem.tag.upper()
						value = elem.text
						if value == None:
							value = ''

				elif 'DATATYPE' in newDocument:
					if elem.tag == newDocument['DATATYPE']:
						# Inside vsData container
						readToDocument = True

				elif not inAttributes:
					elements.append(elem.tag)
					popList.append(True)
					if self.configDir == '':
						if elem.tag == 'MeContext':
							sharedDoc['GNODEB_NAME'] = containerId
							sharedDoc['ENODEB_NAME'] = containerId
							sharedDoc['NODEB_NAME'] = containerId
							sharedDoc['BTS_NAME'] = containerId
						elif elem.tag == 'SubNetwork':
							sharedDoc['RNC_NAME'] = containerId
							sharedDoc['BSC_NAME'] = containerId

					if containerId != None:
						if objectFILO != []:
							objectFILO.append('{0},{1}={2}'.format(objectFILO[-1], re.sub('^vsData', '', elem.tag), containerId))
						else:
							objectFILO.append('{0}={1}'.format(re.sub('^vsData', '', elem.tag), containerId))
						#print objectFILO[-1]

				elif inAttributes and not inContainer:
					counter = elem.tag.upper()
					value = elem.text
					if value == None:
						value = ''


				elem.clear()

			elif event == 'end':
				if elem.tag == 'attributes':
					inAttributes = False

				elif elem.tag == 'vsDataType':
					if value == None:
						value = elem.text

					# Unit Id
					newDocument = copy.deepcopy(sharedDoc)
					newDocument['DATATYPE'] = value
					if value.replace('vsData', '') == elements[-1]:
						newDocument.update(elementAtributes)

					#print '{1} .. {0}'.format(value.replace('vsData', ''), elements[-1])
					if value.replace('vsData', '') == elements[-1]:
						popList.append(False)
					else:
						popList.append(True)

					if elements[-1] != value.replace('vsData', ''):
						if objectFILO != []:
							objectFILO.append('{0},{1}={2}'.format(objectFILO[-1], value.replace('vsData', ''), containerId))
						else:
							objectFILO.append('{0}={1}'.format(value.replace('vsData', ''), containerId))
					newDocument['FDN'] = objectFILO[-1]
					#print objectFILO[-1]
					value = None

				elif elem.tag == 'VsDataContainer':
					# poops the corrent container fdn
					inContainer = False
					readToDocument = False

					if popList[-1]:
						try:
							objectFILO.pop()
						except:
							pass
					popList.pop()

				elif readToDocument:
					if newDocument['DATATYPE'] == elem.tag:
						# creates event and sends it to kafka
						try:
							data_time = familyObj.parseEnvelopeDataTime(newDocument["DATETIME"])
							newDocument["DATETIME"] = newDocument["DATETIME"].replace('T', ' ')
						except ValueError as e:
							logger.warning("Could not build mediationEnvelope due to {0}: ".format(e), __file__)
							continue

						familyObj.clearDocuments()
						familyId = re.sub('^vsData', '', newDocument['DATATYPE'])
						familyObj.setUnitID(familyId.upper())
						if familyId.upper() in ['UTRANCELL']:
							enrichDict = dict()
							try:
								enrichDict['CELL_NAME'] = containerId
								enrichDict['CELL_ID'] = newDocument['LOCALCELLID']
								if 'CELL_ID' not in enrichDict and 'CID' in newDocument:
									enrichDict['CELL_ID'] = newDocument['CID']

								newDocument.update(enrichDict)
							except:
								pass
							try:
								for key in caracterization.keys():
									if containerId in caracterization[key]['CELL_NAMES']:
										sharedDoc['NODEB_NAME'] = key
										newDocument['NODEB_NAME'] = key
							except Exception as e:
								print e
						elif familyId.upper() in ['GERANCELL']:
							enrichDict = dict()
							try:
								enrichDict['CELL_NAME'] = containerId
								enrichDict['CELL_ID'] = newDocument['GERANCELLID']

								newDocument.update(enrichDict)
							except:
								pass
							try:
								for key in caracterization.keys():
									if containerId in caracterization[key]['CELL_NAMES']:
										sharedDoc['BTS_NAME'] = key
										newDocument['BTS_NAME'] = key
							except Exception as e:
								print e

						data_document = {"dataTime": data_time, "granularitySec": newDocument['GRANULARITYPERIOD'], "data": newDocument}
						familyObj.addDocument(data_document)
						self.nextOp(familyObj = familyObj, baseObject = baseObject)
						newDocument = dict()
						if inMemory != None:
							newDocument = inMemory
							inMemory = None
						else:
							readToDocument = False
						continue

					if value == '':
						value = elem.text
					if value == '':
						elem.clear()
						continue

					if counter in newDocument and self.consolidation:
						if self.tech == '3G':
							newDocument[counter] = '{0}/{1}'.format(newDocument[counter], value)
						elif self.tech != '4G':
							newDocument[counter] = '{0},{1}'.format(newDocument[counter], value)
						elif counter in ['RESERVEDBY']:  # and self.tech == '4G'
							newDocument[counter] = '{0}/{1}'.format(newDocument[counter], value)
					elif counter not in newDocument and value not in [None, '']:
						newDocument[counter] = value
					value = None

				elif inAttributes and not inContainer:
					if value == '':
						value = elem.text
					if value == '':
						elem.clear()
						continue
					elementAtributes[counter] = value
					value = None

				elif elements != []:
					if elem.tag == elements[-1]:
						if popList == list():
							elem.clear()
							continue
						if popList[-1]:
							try:
								objectFILO.pop()
							except:
								pass
						popList.pop()
						elements.pop()


				elem.clear()
		del context
