__doc__ = \
	__version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

import json
import os
import pkgutil
from collections import OrderedDict
import src.inputFormats
import src.rules
from lib.functions import xmlReader, writeToFile
import src.outputFormats.json
import src.outputFormats.xml
import src.outputFormats.xml.clientCatalog
import src.outputFormats.xml.operationsCatalog
import src.outputFormats.xml.ossCatalog
import src.validations
from lib.objects.column import column
from lib.versioningLoader import convertData, getCatalog, getLoadingCatalog
from src.merge.xml import clientMerge
from src.merge.xml import ossMerge
from src.merge.xml import operationsMerge
from src.merge.json import loadingCatalogMerge
from src.merge.xml2 import transformerEricsson as dataAnalysis
from src.differences import differencesInCatalogs
from src.altaiaConverter import exportMerge
from lib.Logger import Logger
import time
from src.sqlCreator import sqlGenerator
from src.postgresCreator import postgresGenerator

class MediationCollectorManager():

	def __init__(self):
		self.operations = dict()
		self.collectorConfiguration = None
		self.logger = Logger('processLogger').get()
		pass

	def process(self, operation, data):
		self.logger.debug("  ######### START TIME:			  {:20s} #########".format(time.strftime("%Y.%m.%d %H:%M:%S")))
		if operation == 'CREATE':
			catalogInfo = self.createCatalog(data['vendor'], data['collector'], data['documentation'])
			if data['shelfPath'] not in ['NA', '']:
				catalogInfo = convertData(catalogInfo, data['vendor'], data['collector'], data['shelfPath'])
			self.writeCatalogs(catalogInfo, data)
			# Validate XML output ('lib/validations.json')
			if self.collectorConfiguration['outputFormat']['format'] != 'json':
				self.validateCatalogs(data)
		elif operation == 'MERGE':
			self.mergeCatalogs(data)
			# Validate XML output ('lib/validations.json')
			self.validateCatalogs(data)
		elif operation == 'DIFF':
			differencesInCatalogs.process(data['vendor'], data['collector'], data['baseCatalog'], data['newCatalog'], data['shelfCatalog'], {})
			# Validate XML output ('lib/validations.json')
			self.validateCatalogs(data)
		elif operation == 'SQL':
			self.logger.debug("  ********** {:43s} **********".format('Starting SQL Creation Process'))
			sqlGenerator.process(data)
		elif operation == 'POSQL':
			self.logger.debug("  ********** {:43s} **********".format('Starting PostGresSQL Creation Process'))
			postgresGenerator.process(data)
		elif operation == 'CONVERT':
			self.convertCatalogs(data)
			# Validate XML output ('lib/validations.json')
			self.validateCatalogs(data)
		elif operation == 'NAMF_COUNTERS':
			self.generateNamfCounters(data['baseCatalog'])
		elif operation == 'ALTAIA_EXPORT':
			epMerge = exportMerge
			epMerge.convertByExport(data['baseCatalog'], data['documentation'])

		self.logger.debug("  ######### END TIME:				{:20s} #########".format(time.strftime("%Y.%m.%d %H:%M:%S")))

	# #
	# Processes the data and applies all the rules and corrections needed
	# #
	def createCatalog(self, vendor, collectorConfig, documentPath):

		self.collectorConfiguration = self.getCollectorConfigurations(vendor, collectorConfig)
		self.logger.debug("  ********** {:43s} **********".format('Starting Catalog Creation Process'))
		self.logger.debug("  ********** {:43s} **********".format('Processing information'))
		self.logger.debug("  * Creating Catalog for collector {:30s} *".format(self.collectorConfiguration['collector']['name']))
		self.logger.debug("  * Collector config {:44} *".format(collectorConfig))
		self.logger.debug("  *****************************************************************")
		self.logger.debug("  * Getting Catalog Configuration for {:27s} *".format(collectorConfig))
		print 'Creating catalog using collector configuration "' + collectorConfig + '".\n'
		self.collectorConfiguration['inputFormat']['doc'] = documentPath

		# READ input documentacion
		self.logger.debug("  * Getting Input Configuration format...{:24s} *".format(''))
		inputFormat = self.getInputFormat()
		if inputFormat == None:
			print 'Input Format not Found.'
			self.logger.debug("  * Input Configuration format wasn\'t found {:24s} *".format(''))
			return
		
		print 'Processing data...'
		docFile = self.collectorConfiguration['inputFormat']['doc']
		configDoc = self.collectorConfiguration['inputFormat']['formatConfig']
		data = inputFormat.process(docFile, configDoc, self.collectorConfiguration, self.collectorConfiguration['collector']['vendor'])
		print 'Finish getting data.\n'

		data = self.getPresetFields(data)


		# Apply rules
		self.logger.debug("  ######### START Applying Rules:	{:20s} #########".format(time.strftime("%Y.%m.%d %H:%M:%S")))
		rules = self.getRules()
		for key in rules.keys():
			for packageName in rules[key]:
				for ruleConfig in rules[key][packageName]['config']:
					self.logger.debug("  * Applying the rule: {:42s} *".format(packageName))
					print 'Applying the ' + key + ' rule "' + packageName + '"...'
					rules[key][packageName]['module'].process(data, ruleConfig)
					print 'Rule applied.'
					self.logger.success("* Finish applying the rule: {:35s} *".format(packageName))
		print ''
		self.logger.success("* Finish aplling all the rules. {:31s} *".format(''))

		# Corrections from corrections.json file, are applied in here
		self.logger.debug("  ######### START Corrections:   {:24s} #########".format(time.strftime("%Y.%m.%d %H:%M:%S")))
		if os.path.exists('./config/customization/corrections.json'):
			corrections = json.load(open('./config/customization/corrections.json'), object_pairs_hook=OrderedDict)

			for ossId in corrections.keys():
				if ossId in data.keys():
					unitObj = data[ossId]

					for tag in corrections[ossId]['tags'].keys():
						unitObj.update(tag.upper(), corrections[ossId]['tags'][tag])

					attributesDict = unitObj.attributes
					for attributeId in corrections[ossId]['attributes'].keys():
						if attributeId in attributesDict.keys():
							for tag in corrections[ossId]['attributes'][attributeId].keys():
								if tag.upper() == 'BDCOLNAME':
									unitObj.update('BDCOLNAME', [attributesDict[attributeId].sqlName, corrections[ossId]['attributes'][attributeId][tag]])
								attributesDict[attributeId].update(tag, corrections[ossId]['attributes'][attributeId][tag])

					for unitId in corrections[ossId]['tables'].keys():
						tablesDict = unitObj.tables
						for tableId in tablesDict.keys():
							if tableId == unitId:
								tableObj = tablesDict[tableId]
								for tag in corrections[ossId]['tables'][unitId]['tags'].keys():
									tableObj.update(tag, corrections[ossId]['tables'][unitId]['tags'][tag])
									if tag.upper() == 'ID':
										unitObj.addTable(corrections[ossId]['tables'][unitId]['tags'][tag], unitObj.tables.pop(tableId))

								countersDict = tableObj.counters
								for counterId in corrections[ossId]['tables'][tableId]['counters'].keys():
									if counterId in countersDict.keys():
										for tag in corrections[ossId]['tables'][tableId]['counters'][counterId].keys():
											if tag.upper() == 'BDCOLNAME':
												tableObj.update('BDCOLNAME', [countersDict[counterId].sqlName, corrections[ossId]['tables'][unitId]['counters'][counterId][tag]])
											countersDict[counterId].update(tag, corrections[ossId]['tables'][tableId]['counters'][counterId][tag])
										if 'dbn0type' in corrections[ossId]['tables'][unitId]['counters'][counterId].keys():
											if countersDict[counterId].dbn0type in ['PK', 'ID']:
												unitObj.addAttribute(counterId, countersDict[counterId])
												tableObj.removeCounter(counterId)


			self.logger.debug("  * {:61s} *".format('Corrections were applied.'))
		else:
			self.logger.debug("  * {:61s} *".format('No correction to be applied.'))
		self.logger.success("* Finish applying corrections. {:32s} *".format(''))

		return data

	# #
	# Writes de data into the formats in the collector configuration
	# #
	def writeCatalogs(self, data, config):
		# Create Catalogs
		self.logger.debug("  ######### START Building Catalogs: {:20s} #########".format(time.strftime("%Y.%m.%d %H:%M:%S")))
		try:
			if self.collectorConfiguration['outputFormat']['format'] == 'xml':
				outFormatList = self.getOutputFormat(src.outputFormats.xml.__path__)
			elif self.collectorConfiguration['outputFormat']['format'] == 'json':
				outFormatList = self.getOutputFormat(src.outputFormats.json.__path__)
			else:
				self.logger.error(" Output format directory {:s} wasn't found, setting default 'xml'.".format(self.collectorConfiguration['outputFormat']['format']))
				outFormatList = self.getOutputFormat(src.outputFormats.xml.__path__)
		except:
			self.logger.error(" Output format wasn't found, setting default 'xml'.")
			outFormatList = self.getOutputFormat(src.outputFormats.xml.__path__)

		if outFormatList == dict():
			print 'Output Format not Found.'
			self.logger.debug("  * Output Configuration format wasn\'t found {:23s} *".format(''))
			return
		for outFormat in outFormatList.keys():
			self.logger.debug("  * Applying output format: {:37s} *".format(outFormat))
			outFormatList[outFormat].process(data, self.collectorConfiguration, config)
			self.logger.success("* Finish creating format: {:37s} *".format(outFormat))
		self.logger.success("* Finish building catalogs. {:35s} *".format(''))
		#loadingCatalog.process(data, self.collectorConfiguration)
		print '\n'

	# #
	#   Merges two catalogs and generates de differences between them
	# #
	def mergeCatalogs(self, data):
		if data['mergeConfiguration'] == '':
			data['mergeConfiguration'] = './lib/'
		##dataAnalysis.process(data['vendor'], data['baseCatalog'], data['newCatalog'], data['nomenclature'],mergeConfig['operations'])
		#if data['vendor'].upper() == 'ERICSSON':
		#	mergeConfig = json.load(open(data['mergeConfiguration'] + 'mergeConfiguration.json'), object_pairs_hook=OrderedDict)
		#	catalogData, model, version = dataAnalysis.process(data['vendor'], data['baseCatalog'], data['newCatalog'], data['nomenclature'], mergeConfig)
		#	config = dict()
		#	config['model'] = model
		#	config['version'] =version
		#	config['vendor'] = data['vendor']
		#	config['nameNomenclature'] = data['nomenclature']
		#	config['tech'] = ''
		#	src.outputFormats.xml.clientCatalog.process(catalogData, {"collector":config})
		#	src.outputFormats.xml.ossCatalog.process(catalogData, {"collector": config})
		#	src.outputFormats.xml.operationsCatalog.process(catalogData, {"collector": config, "outputFormat":{"operationsCatalog":{}}})
		#	data['nomenclature'] += '.xml'
		#	return
		#mergeConfig = json.load(open(data['mergeConfiguration'] + 'mergeConfiguration_JSON.json'), object_pairs_hook=OrderedDict)
		#loadingMerge.process(data['vendor'], data['baseCatalog'], data['newCatalog'], data['nomenclature'], mergeConfig['loadingCaltalog'])
		#return

		mergeConfig = json.load(open(data['mergeConfiguration'] + 'mergeConfiguration.json'), object_pairs_hook=OrderedDict)
		#self.logger.debug("  ######### mergeConfig  {:24s} #########".format(mergeConfig))
		operationsMerge.process(data['vendor'], data['baseCatalog'], data['newCatalog'], data['nomenclature'], mergeConfig['operations'])
		clientMerge.process(data['vendor'], data['baseCatalog'], data['newCatalog'], data['nomenclature'], mergeConfig['client'])
		ossMerge.process(data['vendor'], data['baseCatalog'], data['newCatalog'], data['nomenclature'], mergeConfig['oss'])

		#differencesInCatalogs.process(data['vendor'], data['collector'], data['baseCatalog'], data['newCatalog'], './output/' + str(data['numenclature']), {})
		pass

	# #
	# Converts a shelf catalog into a client shelf catalog
	# #
	def convertCatalogs(self, data):
		self.collectorConfiguration = self.getCollectorConfigurations(data['vendor'], data['collector'])
		if data['baseCatalog'].endswith('.xml'):
			unitDict = getCatalog(data['baseCatalog'])
		elif data['baseCatalog'].endswith('.json'):
			unitDict = getLoadingCatalog(data['baseCatalog'])

		# Applies here the customizations from the file Customizations.json (client oriented)
		self.logger.debug("  ######### START Customizations:   {:24s} #########".format(time.strftime("%Y.%m.%d %H:%M:%S")))
		if os.path.exists('./config/customization/Customizations.json'):
			corrections = json.load(open('./config/customization/Customizations.json'), object_pairs_hook=OrderedDict)

			for ossId in corrections.keys():
				if ossId in unitDict.keys():
					unitObj = unitDict[ossId]
					newOssId = ''
					for tag in corrections[ossId]['tags'].keys():
						if tag.upper() == 'OSSID':
							newOssId = corrections[ossId]['tags'][tag]
						else:
							unitObj.update(tag.upper(), corrections[ossId]['tags'][tag])

					attributesDict = unitObj.attributes
					for attributeId in corrections[ossId]['attributes'].keys():
						if attributeId in attributesDict.keys():
							for tag in corrections[ossId]['attributes'][attributeId].keys():
								if tag.upper() == 'BDCOLNAME':
									unitObj.update('BDCOLNAME', [attributesDict[attributeId].sqlName, corrections[ossId]['attributes'][attributeId][tag]])
								attributesDict[attributeId].update(tag, corrections[ossId]['attributes'][attributeId][tag])

					for unitId in corrections[ossId]['tables'].keys():
						tablesDict = unitObj.tables
						for tableId in tablesDict.keys():
							if tableId == unitId:
								newTableId = ''
								tableObj = tablesDict[tableId]
								for tag in corrections[ossId]['tables'][unitId]['tags'].keys():
									if tag.upper() == 'ID':
										newTableId = corrections[ossId]['tables'][unitId]['tags'][tag]
									else:
										tableObj.update(tag, corrections[ossId]['tables'][unitId]['tags'][tag])

								countersDict = tableObj.counters
								for counterId in corrections[ossId]['tables'][tableId]['counters'].keys():
									if counterId in countersDict.keys():
										for tag in corrections[ossId]['tables'][tableId]['counters'][counterId].keys():
											if tag.upper() == 'BDCOLNAME':
												tableObj.update('BDCOLNAME', [countersDict[counterId].sqlName, corrections[ossId]['tables'][unitId]['counters'][counterId][tag]])
											countersDict[counterId].update(tag, corrections[ossId]['tables'][tableId]['counters'][counterId][tag])
										if 'dbn0type' in corrections[ossId]['tables'][unitId]['counters'][
											counterId].keys():
											if countersDict[counterId].dbn0type in ['PK', 'ID']:
												unitObj.addAttribute(counterId, countersDict[counterId])
												tableObj.removeCounter(counterId)

								if newTableId != '':
									unitObj.addTable(newTableId, unitObj.tables.pop(tableId))

					if newOssId != '':
						unitObj = unitDict.pop(ossId)
						unitDict[newOssId] = unitObj

			self.logger.debug("  * {:61s} *".format('Customizations were applied.'))

		# Converts data with shelf or file's passed by command line
		catalogInfo = convertData(unitDict, data['vendor'], data['collector'], data['shelfPath'])
		self.writeCatalogs(catalogInfo, data)

	# #
	# Returns the configuration from the Collector from a specific Vendor
	# #
	def getCollectorConfigurations(self, vendor, collectorName):

		return json.load(open('./collector/'+vendor+'/'+collectorName+'.json'), object_pairs_hook=OrderedDict)

	# #
	#   Gets all the input formats from input folder
	# #
	def getInputFormat(self):
		for importer, packageName, _ in pkgutil.iter_modules(src.inputFormats.__path__):
			if packageName == self.collectorConfiguration['inputFormat']['format']:
				return importer.find_module(packageName).load_module(packageName)
		return None
	
	# #
	#   Gets all the rules/configurations to be applied to the catalog
	# #
	def getRules(self):
		rules = OrderedDict()
		for key in self.collectorConfiguration['rules']:
			rules[key] = OrderedDict()
			for rule in self.collectorConfiguration['rules'][key]:
				for importer, packageName, _ in pkgutil.iter_modules(src.rules.__path__):

					if packageName == rule:
						rules[key][packageName] = dict()
						rules[key][packageName]['module'] = importer.find_module(packageName).load_module(packageName)
						rules[key][packageName]['config'] = self.collectorConfiguration['rules'][key][rule]
						break
		return rules

	# #
	#   Gets all the output formats from output folder
	# #
	def getOutputFormat(self, formatDir):
		outFormatList = OrderedDict()
		for importer, packageName, xx in pkgutil.iter_modules(formatDir):
			if packageName in self.collectorConfiguration['outputFormat']['catalogs']:
				outFormatList[packageName] = importer.find_module(packageName).load_module(packageName)
		return outFormatList

	# #
	#   Get presetField configurations from config/inputConfig for attributes
	#   With this the interval is being taken in account as an attribute yet being a counter
	# #
	def getPresetFields(self, data):
		if not os.path.exists('./config/presetFields/' + self.collectorConfiguration['inputFormat']['presetFields'] + '.json'):
			print("[warning] presetFields config file '{0}.json' couldn't be found ".format(self.collectorConfiguration['inputFormat']['presetFields']))
			return None

		presetFile = json.load(open('./config/presetFields/' + self.collectorConfiguration['inputFormat']['presetFields'] + '.json'))
		catalogType = self.collectorConfiguration['collector']['collectorType']

		for unitId in data.keys():

			for columnInfo in presetFile[catalogType]:
				columnObj = column()
				
				# default values
				_typeCust = columnInfo['dataUnit']
				_name = columnInfo['id']
				
				# possible overriding of "typeCust"
				if 'correctTypeCust' in columnInfo and columnInfo['correctTypeCust'] != '' and columnInfo['correctTypeCust'] != 'NA':
					_typeCust = columnInfo['correctTypeCust']
				
				# possible overriding of "name"
				if 'correctName' in columnInfo and columnInfo['correctName'] != '' and columnInfo['correctName'] != 'NA':
					_name = columnInfo['correctName']
				
				# column creation
				columnObj.create(columnInfo['id'], _name, columnInfo['udn'], columnInfo['sqlName'], columnInfo['desc'], columnInfo['dbn0type'], columnInfo['dataType'], _typeCust, columnInfo['dataUnit'], columnInfo['dataUnit'], '')
				
				if columnObj in data[unitId].attributes.keys():
					self.logger.warning(' * [getPresetFields] Column id \"{:s}\" already exists in Table \"{:s}\", information was discarted * '.format(columnInfo['id'], unitId))
					continue

				unitObj = data[unitId]
				if columnInfo['dbn0type'] in ['ID', 'PK']:
					data[unitId].addAttribute(columnInfo['id'].upper(), columnObj)
					for tableId in unitObj.tables.keys():
						tableObj = unitObj.getTable(tableId)
						if columnInfo['id'].upper() in tableObj.counters.keys():
							tableObj.removeCounter(columnInfo['id'].upper())
				else:
					for tableId in unitObj.tables.keys():
						tableObj = unitObj.getTable(tableId)
						if columnInfo['id'].upper() not in tableObj.counters.keys():
							tableObj.addCounter(columnInfo['id'].upper(), columnObj)
		return data

	# #
	#   Applies the validations from the function getValidations, validating the final catalog
	# #
	def validateCatalogs(self, commandConfig):
		log = Logger('validationsLogger').get()
		if self.collectorConfiguration is not None:
			name = './output/' + self.collectorConfiguration['collector']['nameNomenclature'] + '.xml'
			# Client #
			root = xmlReader(name.replace('#', 'client'))
			log.debug('##########################################################################################################################################')
			log.debug('##      Creating catalogs Vendor: {:20s}    Model: {:14s}     Version: {:20s}    Tech: {:10s}   ##'.format(self.collectorConfiguration['collector']['vendor'], self.collectorConfiguration['collector']['model'], self.collectorConfiguration['collector']['version'], self.collectorConfiguration['collector']['tech']))
			log.debug('##########################################################################################################################################')
		else:
			if commandConfig['nomenclature'] not in ['', 'n']:
				name = './output/' + commandConfig['nomenclature']
			else:
				name = commandConfig['baseCatalog']
			# Client #
			root = xmlReader(name.replace('#', 'client'))
			log.debug('##########################################################################################################################################')
			log.debug('##      Creating catalogs Vendor: {:20s}    Model: {:14s}     Version: {:20s}    Tech: {:10s}   ##'.format(root.get('vendor'), root.get('model'), root.get('ossversion'), root.find('table').get('tech')))
			log.debug('##########################################################################################################################################')

		config = json.load(open('./lib/configuration.json'))

		validationsList = self.getValidations()

		data = dict()
		tableNameList = list()
		for table in root.findall('table'):
			# Validate Table
			tableId = table.get('id').upper()
			tableName = table.get('tableName').upper()
			if tableName in tableNameList:
				log.warning('Duplicated tableName for tableId \"{:s}\".'.format(tableId))
			else:
				tableNameList.append(tableName)
			data[tableId] = list()
			for validation in validationsList['client']['table']:
				validation.process(table, config['unit'])
			for column in table.findall('column'):
				# Validate Column
				bdcolname = column.get('bdcolname').upper()
				if bdcolname in data[tableId]:
					log.warning('Duplicated bdcolname \"{:s}\" for columnId \"{:s}\" in tableId \"{:s}\".'.format(bdcolname, column.get('id'), tableId))
				else:
					data[tableId].append(bdcolname)
				for validation in validationsList['client']['column']:
					validation.process(column, tableId, config['item'])

		# OSS #
		root = xmlReader(name.replace('#', 'oss'))
		for unit in root.findall('unit'):
			# Validate Unit
			unitId = unit.get('id')
			for validation in validationsList['oss']['unit']:
				validation.process(unit, config['unit'])
			for titem in unit.findall('item'):
				# Validate Item
				for validation in validationsList['oss']['item']:
					validation.process(titem, unitId, config['unit'])

		# Operations #
		root = xmlReader(name.replace('#', 'operations'))
		for unit in root.findall('unit'):
			# Validate Unit
			unitId = unit.get('id')
			for validation in validationsList['operations']['unit']:
				validation.process(unit, config['unit'])
			for titem in unit.findall('item'):
				# Validate Item
				for validation in validationsList['operations']['item']:
					validation.process(titem, unitId, config['unit'])

		log.debug('##########################################################################################################################################')

	# #
	#   Gets the validations to validate on src/validations folder, to validate the catalog
	# #
	def getValidations(self):
		validationsList = dict()
		config = json.load(open('./lib/validations.json'))
		for catalog in config.keys():
			validationsList[catalog] = dict()
			for tag in config[catalog].keys():
				validationsList[catalog][tag] = list()
				for importer, packageName, xx in pkgutil.iter_modules(src.validations.__path__):
					if packageName in config[catalog][tag]:
						validationsList[catalog][tag].append(importer.find_module(packageName).load_module(packageName))
		return validationsList

	# #
	# Generates sql for the two new field's needed for the na-mf
	#   SOURCE_ID
	#   CONTENT_ID
	# #
	def generateNamfCounters(self, catalogPath):
		self.logger.debug("  ********** {:43s} **********".format('Starting Catalog Creation Process'))
		self.logger.debug("  ********** {:43s} **********".format('Processing information'))
		self.logger.debug("  * Catalog base {:30s} *".format(os.path.basename(catalogPath)))
		self.logger.debug("  *****************************************************************")
		self.logger.debug("  * Validating extension {:40} *".format(''))
		tableNameList = list()
		if catalogPath.endswith('.json'):
			self.logger.debug("  * Processing JSON extension {:35} *".format(''))
			#a fazer
			pass
		elif catalogPath.endswith('.xml'):
			self.logger.debug("  * Processing XML extension {:36} *".format(''))
			root = xmlReader(catalogPath)
			for tableXml in root.findall('table'):
				if tableXml.findall('column') != []:
					tableNameList.append(tableXml.get('tableName'))
		else:
			self.logger.error('File "{:s}" extension is not accepted'.format(os.path.basename(catalogPath)))
			return

		data = ''
		for tableName in tableNameList:
			data += 'ALTER TABLE {:s} ADD (SOURCE_ID VARCHAR2(256));\n'.format(tableName)
			data += 'ALTER TABLE {:s} ADD (CONTENT_ID VARCHAR2(256));\n'.format(tableName)

		writeToFile('na-mf_newCounters.sql', data)
