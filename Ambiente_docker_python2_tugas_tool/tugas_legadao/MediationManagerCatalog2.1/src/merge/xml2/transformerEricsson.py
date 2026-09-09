__doc__ = \
	__version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

from xml.etree.ElementTree import Element
import xml.etree.ElementTree as ET
from lib.functions import xmlReader, writeToXML
import os, re, json, copy
from lib.objects.unit import unit
from lib.objects.table import table
from lib.objects.column import column
from lib.Logger import Logger
from collections import OrderedDict
import pkgutil
import src.merge.xml2.operations

# #
# THIS IS THE LOADING DATA PART
# Merges two XML catalogs into one, being the baseCatalogPath the base for the output
# #
def process(vendor, baseCatalogPath, newCatalogPath, numenclature, config):
	logger = Logger('processLogger').get()

	baseData, baseModel, baseVersion = getClientStruct(xmlReader(baseCatalogPath.replace('#', 'client')), dict())
	baseData = getOssStruct(xmlReader(baseCatalogPath.replace('#', 'oss')), baseData)
	baseData = getOperationsStruct(xmlReader(baseCatalogPath.replace('#', 'operations')), baseData)

	tablesMapping = dict()
	for unitOssId in baseData.keys():
		unitOssId = unitOssId.upper()
		unitObj = baseData[unitOssId]
		tablesMapping[unitOssId] = dict()

		for tableId in unitObj.tables.keys():
			tableObj = unitObj.tables[tableId]
			tableUdn = tableObj.udn.upper()
			tablesMapping[unitOssId][tableUdn] = tableId.upper()

	newData, newModel, newVersion = getClientStruct(xmlReader(newCatalogPath.replace('#', 'client')), dict())
	newData = getOssStruct(xmlReader(newCatalogPath.replace('#', 'oss')), newData)
	newData = getOperationsStruct(xmlReader(newCatalogPath.replace('#', 'operations')), newData)

	baseData = mergeData(baseData, newData, tablesMapping, config)

	return baseData, baseModel, baseVersion +'/'+ newVersion

# #
# Reads and converts client catalog data to program acceptable data format
# #
def getClientStruct(root, data):
	logger = Logger('processLogger').get()

	for tableXml in root.findall('table'):
		ossId = tableXml.get('ossId').upper()
		if ossId not in data.keys():
			unitObj = unit()
			unitObj.create(tableXml.get('ossId'), tableXml.get('ossId'), '', '', '')
			#unitObj.create(ossId, tableXml.get('id'), '', '', '')
			unitObj.tech = tableXml.get('tech')
			data[ossId] = unitObj
		else:
			unitObj = data[ossId]

		tableId = tableXml.get('id').upper()
		if tableId in unitObj.tables.keys():
			tableObj = unitObj.tables[tableId]
			pass
		else:
			tableObj = table()
			tableObj.create(tableId, tableXml.get('ossId'), tableXml.get('tableName'), tableXml.get('udn'))
			tableObj.update('ACTIVE', tableXml.get('active'))
			if re.search(ossId + '_(\d+)$', tableId) is not None:
				tableObj.partitionOf = ossId
			unitObj.addTable(tableId.upper(), tableObj)
			for attr in tableXml.attrib.keys():
				tableObj.add(attr, tableXml.get(attr).strip(), 'client')

		for columnXml in tableXml.findall('column'):
			columnId = columnXml.get('id')
			if columnId.upper() in tableObj.counters.keys():
				logger.warning(' * [versioningLoader] Duplicated column id \"{:s}\" was found on table \"{:s}\" * '.format(columnId, tableId))
				continue
			columnObj = column()
			columnObj.create(columnId, '', columnXml.get('udn'), columnXml.get('bdcolname'), '', columnXml.get('dbn0type'), columnXml.get('bdtype'), '', '', '', 0)
			if columnObj.dbn0type in ['PK', 'ID']:
				unitObj.addAttribute(columnId.upper(), columnObj)
			else:
				tableObj.addCounter(columnId.upper(), columnObj)
	return data, root.attrib['model'], root.attrib['ossversion']

# #
# Reads and converts oss catalog data to program acceptable data format
# #
def getOssStruct(root, data):
	logger = Logger('processLogger').get()
	#measuredobjects
	for unitXml in root.findall('unit'):
		ossId = unitXml.get('ossId').upper()
		if ossId not in data.keys():
			logger.error(' * [versioningLoader] ossId \"{:s}\" was not found in client catalog. * '.format(ossId))
		else:
			unitObj = data[ossId]
			for attr in unitXml.attrib.keys():
					unitObj.add(attr, unitXml.get(attr), 'oss')

			tableList = unitObj.tables
			for itemXml in unitXml.findall('item'):
				itemId = itemXml.get('id').upper()
				if itemId in unitObj.attributes.keys():
					counterObj = unitObj.attributes[itemId]
					for attr in itemXml.attrib.keys():
						counterObj.add(attr, itemXml.get(attr).strip(), 'oss')
					continue

				isMissing = True
				for tableId in tableList.keys():
					tableObj = tableList[tableId]
					if itemId in tableObj.counters.keys():
						isMissing = False
						counterObj = tableObj.counters[itemId]
						for attr in itemXml.attrib.keys():
							counterObj.add(attr, itemXml.get(attr).strip(), 'oss')

				if isMissing:
					logger.warning(' * [versioningLoader] itemId \"{:s}\" from ossId \"{:s}\" was not found in client catalog. * '.format(itemId, ossId))
	return data

# #
# Reads and converts operations catalog data to program acceptable data format
# #
def getOperationsStruct(root, data):
	logger = Logger('processLogger').get()

	for unitXml in root.findall('unit'):
		ossId = unitXml.get('id').upper()
		if ossId in data.keys():
			unitObj = data[ossId]
			for opXml in unitXml.findall('operation'):
				unitObj.addOperation('unit', ossId, opXml)
			for itemXml in unitXml.findall('item'):
				itemId = itemXml.get('id').upper()
				for opXml in itemXml.findall('operation'):
					unitObj.addOperation('item', itemId, opXml)
		else:
			#criar unit unica para tal
			unitObj = unit()
			unitObj.create(ossId, ossId, '', '', '')
			data[ossId] = unitObj
			for opXml in unitXml.findall('operation'):
				unitObj.addOperation('unit', ossId.upper(), opXml)
			for itemXml in unitXml.findall('item'):
				itemId = itemXml.get('id').upper()
				for opXml in itemXml.findall('operation'):
					unitObj.addOperation('item', itemId, opXml)
	return data

def insert_key_value(a_dict, key, pos_key, value):
	new_dict = OrderedDict()
	for k, v in a_dict.items():
		if k == pos_key:
			new_dict[key] = value  # insert new key
		new_dict[k] = v
	return new_dict

def mergeData(baseData, newData, tablesMapping, config):

	for unitId in newData.keys():
		if unitId not in baseData.keys():
			baseData[unitId] = copy.deepcopy(newData[unitId])
			continue

		newUnitObj = newData[unitId]
		baseUnitObj = baseData[unitId]

		for attr in config['unit'].keys():
			applyConfig(attr.upper(), config['unit'][attr], baseUnitObj, newUnitObj.get(attr))

		baseUnitObj = mergeAttributes(baseUnitObj, newUnitObj, config['column'])

		mergeOperations(baseUnitObj, newUnitObj)

		tableToAdd = list()

		for newTableId in newUnitObj.tables.keys():
			newTableObj = newUnitObj.getTable(newTableId)
			newTableUdn = newTableObj.udn.upper()

			if '_newCounter' in newTableUdn:
				newTableUdn = baseUnitObj.getTable(unitId).udn.upper()

			if newTableUdn not in tablesMapping[unitId].keys():
				if newUnitObj.typeId.upper() not in tablesMapping[unitId].keys():
					baseUnitObj.addTable(newTableId, copy.deepcopy(newTableObj))
					tablesMapping[unitId][newTableObj.udn.upper()] = newTableId
					baseUnitObj.addTable(newTableId, newTableObj)
					continue

				number = getUnitValue(baseUnitObj) + 1
				newId = '{0}_{1}'.format(baseUnitObj.typeId, str(number))
				newTableObj = copy.deepcopy(newTableObj)
				newTableObj.update('ID', newId)
				newTableObj.update('TABLENAME', newId.upper())
				baseUnitObj.addTable(newId.upper(), newTableObj)
				tablesMapping[unitId][newTableObj.udn.upper()] = newId.upper()
				baseUnitObj.addTable(newId.upper(), newTableObj)
				continue

			baseTableObj = baseUnitObj.getTable(tablesMapping[unitId][newTableUdn])
			for attr in config['table'].keys():
				applyConfig(attr.upper(), config['table'][attr], baseTableObj, newTableObj.get(attr))

			mergeCounters(baseUnitObj, baseTableObj, newTableObj, config['column'], tablesMapping)

	return baseData

def mergeCounters(baseUnitObj, baseTableObj, newTableObj, config, tablesMapping):

	for counterId in newTableObj.counters.keys():
		counterFound = False

		newCounterObj = newTableObj.getCounter(counterId)

		if counterId in baseTableObj.counters.keys():
			for attr in config.keys():
				applyConfig(attr.upper(), config[attr], baseTableObj.getCounter(counterId), newCounterObj.get(attr))
			continue
		if counterId.upper() in baseTableObj.counters.keys():
			for attr in config.keys():
				applyConfig(attr.upper(), config[attr], baseTableObj.getCounter(counterId.upper()), newCounterObj.get(attr))
			continue

		if counterId in baseUnitObj.attributes.keys() or counterId.upper() in baseUnitObj.attributes.keys():
			continue

		if len(baseTableObj.counters.keys()) + len(baseUnitObj.attributes.keys()) >= 970:
			try:
				subTables = re.findall("({0}_NEWCOUNTERS[^',]*)".format(baseTableObj.udn.upper()), str(tablesMapping[baseUnitObj.typeId.upper()].keys()).strip())
				if subTables != []:
					subTables.sort()
					subTableObj = None
					for subTableId in subTables:
						subTableObj = baseUnitObj.getTable(tablesMapping[baseUnitObj.typeId.upper()][subTableId])
						if counterId in subTableObj.counters.keys():
							counterFound = True
							break
					if counterFound:
						continue

					if len(subTableObj.counters.keys()) + len(baseUnitObj.attributes.keys()) >= 970:
						newSubTableObj = table()
						try:
							tableNumber = int(re.search(r'_(\d+)$', baseUnitObj.tables.keys()[-1]).group(1)) +1
						except:
							tableNumber = 0
						udn = re.sub(r'_(\d+)$', '', subTableObj.udn)
						newSubTableObj.create(baseUnitObj.typeId + '_' + str(tableNumber), baseUnitObj.typeId, baseUnitObj.typeId + '_' + str(tableNumber), udn + '_' + str(tableNumber))
						newSubTableObj.addCounter(counterId, newTableObj.getCounter(counterId))
						baseUnitObj.addTable(newSubTableObj.typeId, newSubTableObj)
						#print 'added1: ' + counterId
						continue
					else:
						subTableObj.addCounter(counterId, newTableObj.getCounter(counterId))
					#print 'added2: ' + counterId
					continue
			except:
				#print 'added3: ' + counterId
				newSubTableObj = table()
				newSubTableObj.create(baseUnitObj.typeId + '_0', baseUnitObj.typeId, baseUnitObj.typeId + '_0', baseUnitObj.typeId + '_newCounters')
				newSubTableObj.addCounter(counterId, newTableObj.getCounter(counterId))
				baseUnitObj.addTable(newSubTableObj.typeId.upper(), newSubTableObj)
				continue
		baseTableObj.addCounter(counterId, newCounterObj)
		#print 'added4: ' + counterId

def mergeAttributes(baseUnitObj, newUnitObj, config):

	for attributeId in newUnitObj.attributes.keys():
		if attributeId in baseUnitObj.attributes.keys():
			for attr in config.keys():
				applyConfig(attr.upper(), config[attr], baseUnitObj.getAttribute(attributeId), newUnitObj.getAttribute(attributeId).get(attr))
			continue
		if attributeId in baseUnitObj.getCountersList():
			continue
		baseUnitObj.addAttribute(attributeId, newUnitObj.getAttribute(attributeId))
	return baseUnitObj

def getUnitValue(unitObj):
	try:
		tableList = unitObj.tables.keys()
		tableList.sort()
		try:
			base = int(re.search(r'_(\d+)$', tableList[-1]).group(1))
		except:
			base = 0
		for tmp in reversed(tableList):
			try:
				value = int(re.search(r'_(\d+)$', tmp).group(1))
				if value > base:
					return value
			except:
				pass
		return base
	except:
		return 0

def applyConfig(attr, operation, baseObj, newObjValue):
	if operation == 'KEEP':
		return
	elif operation == 'UPDATE' and newObjValue != None:
		baseObj.update(attr, newObjValue)
	elif operation == 'REMOVE':
		baseObj.remove(attr)
	else:
		try:
			if newObjValue in [None, '']: return
			elif baseObj.get(attr) in [None,'']: return
			operation, sepChar = operation
			if operation == 'CONCAT':
				if baseObj.get(attr) != '' and baseObj.get(attr) != newObjValue:
					baseObj.update(attr, baseObj.get(attr) + sepChar + newObjValue)
				else:
					baseObj.update(attr, newObjValue)
		except Exception as ex:
			print ex

def mergeOperations(baseObj, newObj):

	operations = getOperations()
	for level in newObj.operations.keys():
		if level not in baseObj.operations.keys():
			baseObj.addOperationLevel(level, newObj.getOperations(level))
			continue

		for newOpId in newObj.getOperations(level).keys():
			if newOpId not in baseObj.getOperations(level).keys():
				baseObj.addOperation(level, newOpId, newObj.getOperation(level, newOpId))
				continue

			for newOpXML in newObj.getOperation(level, newOpId):
				newOpName = newOpXML.get('type')
				for baseOpXML in baseObj.getOperation(level, newOpId):
					baseOpName = baseOpXML.get('type')
					#print newOpName + ' - ' + baseOpName
					if newOpName == baseOpName:
						if newOpName not in operations.keys():
							print 'missing operation'
							break

						operations[newOpName].process(baseOpXML, newOpXML)

# #
# Loads all operations that are configurations in the dir operations
# #
def getOperations():
	operations = dict()
	for importer, packageName, _ in pkgutil.iter_modules(src.merge.xml2.operations.__path__):
		operations[packageName] = importer.find_module(packageName).load_module(packageName)
	return operations
