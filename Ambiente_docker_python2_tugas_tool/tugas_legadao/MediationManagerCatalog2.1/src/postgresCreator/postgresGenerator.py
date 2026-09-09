__doc__ = \
	__version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

from xml.etree.cElementTree import Element
from collections import OrderedDict
import xml.etree.cElementTree as ET
from lib.functions import xmlReader
import time, os, re
import json
import xlrd
from lib.Logger import Logger
import pkgutil
import src.postgresCreator.modules

# #
# Creates the needed sql queries with an excel as base, or without the excel to create all
# #
def process(config):
	logger = Logger('processLogger').get()
	logger.debug("  ######### START TIME:              {:20s} #########".format(time.strftime("%Y.%m.%d %H:%M:%S")))

	#data['vendor'], data['baseCatalog'], data['nomenclature'], data['compressedFlag'], data['dateIndex']

	if config['baseCatalog'].endswith('.xml'):
		catalog, vendor = getXMLInfo(re.sub(r'#', 'client', config['baseCatalog']))
		config['vendor'] = vendor
	elif config['baseCatalog'].endswith('.json'):
		catalog = getJsonInfo(config['baseCatalog'])
		if 'ERICSSON' in config['baseCatalog']:
			config['vendor'] = 'ERICSSON'
		elif 'HUAWEI' in config['baseCatalog']:
			config['vendor'] = 'HUAWEI'
		elif 'NOKIA' in config['baseCatalog']:
			config['vendor'] = 'NOKIA'

	if config['documentation'] != 'd':
		data = getExcelInfo(config['documentation'])
	else:
		data = OrderedDict()
		data['table'] = OrderedDict()
		data['table']['new'] = catalog.keys()
		data['table']['remove'] = list()
		data['table']['change'] = dict()
		data['column'] = OrderedDict()
		data['column']['new'] = OrderedDict()
		data['column']['remove'] = dict()
		data['column']['change'] = dict()

	modules = getModules()
	for module in modules.keys():
		modules[module].generate(data, catalog, config)

	logger.debug("  ######### END TIME:                {:20s} #########".format(time.strftime("%Y.%m.%d %H:%M:%S")))

# #
# Gets the diff excel data, in the client sheet, to generate the queries needed
# #
def getExcelInfo(fileName):
	logger = Logger('processLogger').get()

	if not os.path.isfile(fileName):
		print("Documentation with the path \"{:3s}\" wasn\'t found.".format(fileName))
		logger.error("  * Documentation with the path \"{:3s}\" wasn\'t found. * ".format(fileName))
		return None

	data = OrderedDict()
	data['table'] = OrderedDict()
	data['table']['new'] = list()
	data['table']['remove'] = list()
	data['table']['change'] = OrderedDict()
	data['column'] = OrderedDict()
	data['column']['new'] = OrderedDict()
	data['column']['remove'] = OrderedDict()
	data['column']['change'] = OrderedDict()

	workBook = xlrd.open_workbook(fileName)
	sheet = workBook.sheet_by_name('consolidadoClient')
	for row in range(2, sheet.nrows):
		state = str(sheet.cell(row, 9).value).encode("utf-8")
		tableName = str(sheet.cell(row, 1).value).encode("utf-8").upper()
		if 'TABLE' in state.upper():
			if 'NEW TABLE' == state.upper():
				data['table']['new'].append(tableName)
			elif 'REMOVED TABLE' == state.upper():
				data['table']['remove'].append(tableName)
			elif 'CHANGED TABLE' == state.upper():
				tableName = str(sheet.cell(row, 7).value).encode("utf-8")
				attribute = str(sheet.cell(row, 6).value).encode("utf-8")
				if tableName not in data['table']['change'].keys():
					data['table']['change'][tableName] = dict()
				if attribute not in data['table']['change'][tableName].keys():
					data['table']['change'][tableName][attribute] = str(sheet.cell(row, 8).value).encode("utf-8")
		elif 'COLUMN' in state.upper():
			if 'NEW COLUMN' == state.upper():
				if tableName not in data['column']['new'].keys():
					data['column']['new'][tableName] = list()
				bdcolname = str(sheet.cell(row, 4).value).encode("utf-8").upper()
				if bdcolname in data['column']['new'][tableName]:
					logger.warning('  * In unit \"{:2s}\" duplicated bdcolumn name \"{:3s}\"'.format(tableName, bdcolname))
					continue
				data['column']['new'][tableName].append(bdcolname)
			elif 'REMOVED COLUMN' == state.upper():
				if tableName not in data['column']['remove'].keys():
					data['column']['remove'][tableName] = list()
				bdcolname = str(sheet.cell(row, 4).value).encode("utf-8").upper()
				if bdcolname in data['column']['remove'][tableName]:
					logger.warning('  * In unit \"{:2s}\" duplicated bdcolumn name \"{:3s}\"'.format(tableName, bdcolname))
					continue
				data['column']['remove'][tableName].append(bdcolname)
			elif 'CHANGED COLUMN' == state.upper() and str(sheet.cell(row, 10).value).encode("utf-8") == 'N':
				attribute = str(sheet.cell(row, 6).value).encode("utf-8")
				bdcolname = str(sheet.cell(row, 4).value).encode("utf-8").upper()
				if tableName not in data['column']['change'].keys():
					data['column']['change'][tableName] = dict()
				if bdcolname not in data['column']['change'][tableName].keys():
					data['column']['change'][tableName][bdcolname] = dict()
				if attribute in data['column']['change'][tableName][bdcolname].keys():
					logger.warning('  * In unit \"{:2s}\" duplicated change attribute \"{:s}\" for bdcolname \"{:3s}\"'.format(tableName, attribute, bdcolname))
					continue
				# if changes to bdcolname, needs to save the old name, as the new name is already the 'bdcolname' variable
				if attribute == 'bdcolname':
					data['column']['change'][tableName][bdcolname][attribute] = str(sheet.cell(row, 7).value).encode("utf-8")
				else:
					data['column']['change'][tableName][bdcolname][attribute] = str(sheet.cell(row, 8).value).encode("utf-8")
	return data

# #
# Gets the xml catalog data for configuration of the queries
# #
def getXMLInfo(fileName):
	logger = Logger('processLogger').get()
	if not os.path.isfile(fileName):
		logger.error("  * Catalog with the path \"{:3s}\" wasn\'t found.".format(fileName))
		return None

	root = xmlReader(fileName)
	vendor = root.get("vendor")

	catalog = OrderedDict()

	for table in root.findall('table'):
		tableName = table.get('tableName').upper()
		if tableName in catalog:
			logger.warning('  * Table \"{:3s}\" has tableName \"{:3s}\" duplicated.'.format(table.get('id'), tableName))
			continue

		if table.findall('column') == []:
			continue

		catalog[tableName] = OrderedDict()
		for column in table.findall('column'):
			bdcolname = column.get('bdcolname').upper()
			if bdcolname in catalog[tableName]:
				logger.warning(
					'  * In table \"{:3s}\", the column \"{:3s}\" has bdcolname \"{:3s}\" duplicated.'.format(table.get('id'), column.get('id'), bdcolname))
				continue
			catalog[tableName][bdcolname] = OrderedDict()
			catalog[tableName][bdcolname]['dbn0type'] = column.get('dbn0type')
			catalog[tableName][bdcolname]['bdtype'] = column.get('bdtype')

	return catalog, vendor

# #
# Gets the json catalog data for configuration of the queries
# #
def getJsonInfo(fileName):
	logger = Logger('processLogger').get()
	if not os.path.isfile(fileName):
		logger.error("  * Catalog with the path \"{:3s}\" wasn\'t found.".format(fileName))
		return None

	root = json.load(open(fileName), object_pairs_hook=OrderedDict)

	catalog = OrderedDict()

	for unitObj in root['measUnits']:
		tableName = unitObj['tableName']
		if tableName in catalog:
			logger.warning('  * Table \"{:3s}\" has tableName \"{:3s}\" duplicated.'.format(unitObj['id'], tableName))
			continue

		if unitObj['measItems'] == list():
			continue

		catalog[tableName] = OrderedDict()
		for itemObj in unitObj['measItems']:
			bdcolname = itemObj['columnName']
			if bdcolname in catalog[tableName]:
				logger.warning(
					'  * In table \"{:3s}\", the column \"{:3s}\" has bdcolname \"{:3s}\" duplicated.'.format(unitObj['id'], itemObj['id'], bdcolname))
				continue
			catalog[tableName][bdcolname] = OrderedDict()
			catalog[tableName][bdcolname]['dbn0type'] = itemObj['measItemType']
			catalog[tableName][bdcolname]['bdtype'] = itemObj['type']
			catalog[tableName][bdcolname]['name'] = unitObj['name']

	return catalog

# #
# Loads all sql query creators in dir modules
# #
def getModules():
	modules = dict()
	for importer, packageName, xx in pkgutil.iter_modules(src.postgresCreator.modules.__path__):
		modules[packageName] = importer.find_module(packageName).load_module(packageName)
	return modules