__doc__ = \
	__version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

from xml.etree.ElementTree import Element
import xml.etree.ElementTree as ET
from lib.functions import xmlReader, writeToXML
import os, re, json
from lib.functions import xmlReader
from lib.objects.unit import unit
from lib.objects.table import table
from lib.objects.column import column
from lib.Logger import Logger
from collections import OrderedDict
import pkgutil
import src.merge.xml.operations

# #
# THIS IS THE LOADING DATA PART
# Merges two XML catalogs into one, being the baseCatalogPath the base for the output
# #
def process(vendor, baseCatalogPath, newCatalogPath, numenclature, config):
	logger = Logger('processLogger').get()

	baseData, baseMatchId, baseModel, baseVersion = getClientStruct(xmlReader(baseCatalogPath.replace('#', 'client')), dict())
	baseData = getOssStruct(xmlReader(baseCatalogPath.replace('#', 'oss')), baseData)
	baseData = getOperationsStruct(xmlReader(baseCatalogPath.replace('#', 'operations')), baseData, baseMatchId)

	unitSplitId = dict()
	for ossId in baseData.keys():
		operations = baseData[ossId].operations
		try:
			for unitId in operations['unit'].keys():
				unitId = unitId.upper()
				for op in operations['unit'][unitId]:
					if op.attrib['type'].startswith('unitSplit'):
						if unitId not in unitSplitId.keys():
							unitSplitId[unitId] = list()
						for rg in op.find('field').findall('regex'):
							if rg.attrib['newunit'] not in unitSplitId[unitId]:
								unitSplitId[unitId].append((rg.attrib['newunit'],rg.attrib['pattern']))
		except:
			pass

	toChange = dict()
	newData, newMatchId, newModel, newVersion = getClientStruct(xmlReader(newCatalogPath.replace('#', 'client')), dict())
	newData = getOssStruct(xmlReader(newCatalogPath.replace('#', 'oss')), newData)
	newData = getOperationsStruct(xmlReader(newCatalogPath.replace('#', 'operations')), newData, newMatchId)

	for ossId in newData.keys():
		if ossId.upper() in unitSplitId.keys():
			newUnitObj = newData[ossId]
			for operId in newUnitObj.operations['item'].keys():
				for operation in newUnitObj.operations['item'][operId]:
					if 'applyRegex' == operation.attrib['type']:
						for rg in operation.findall('regex'):
							ptn = re.sub(r'\(.+?\)', '.+?', rg.attrib['pattern'].replace('$', ''))
							for uId, uPt in unitSplitId[ossId.upper()]:
								if ptn == uPt:
									newData = insert_key_value(newData, uId, ossId, newData[ossId])
									newData[uId].typeId = uId
									for tableId in newUnitObj.tables.keys():
										tableObj = newUnitObj.tables[tableId]
										tableObj.update('TABLENAME', uId)
										tableObj.update('UDN', uId)
										tableObj.update('OSSID', uId)
										tableObj.update('ID', uId)
										toChange[ossId] = uId
										try:
											newUnitObj.update('TABLEID', (ossId.upper(), uId))
										except Exception as ex:
											logger.error(ex)
											return
									newData.pop(ossId)
									logger.warning("The ossId and id of table {:s} was converted to {:s}, with base in unitSplit".format(uId, ossId))
									break

	for ossId in newData.keys():
		if ossId in toChange.keys():
			newData = insert_key_value(newData, toChange[ossId], ossId, newData[ossId])
			newData.pop(ossId)
			unitObj = newData[toChange[ossId]]
			if ossId.upper() in ['AGGREGAT_NTHLRFE','AGGREGAT']:
				for tableId in unitObj.tables.keys():
					tableObj = unitObj.tables[tableId]

	# Falta o merge
	baseData = mergeData(baseData, newData, config)

	return baseData, baseModel, baseVersion +'/'+ newVersion

# #
# Reads and converts client catalog data to program acceptable data format
# #
def getClientStruct(root, data):
	logger = Logger('processLogger').get()
	matchId = dict()

	for tableXml in root.findall('table'):
		ossId = tableXml.get('ossId').upper()
		if ossId not in data.keys():
			unitObj = unit()
			unitObj.create(ossId, ossId, '', '', '')
			#unitObj.create(ossId, tableXml.get('id'), '', '', '')
			unitObj.tech = tableXml.get('tech')
			data[ossId] = unitObj
		else:
			unitObj = data[ossId]

		tableId = tableXml.get('id')
		if tableId in unitObj.tables.keys():
			tableObj = unitObj.tables[tableId].upper()
			pass
		else:
			matchId[tableId] = ossId
			tableObj = table()
			tableObj.create(tableId, tableXml.get('ossId'), tableXml.get('tableName'), tableXml.get('udn'))
			if re.search(ossId + '_(\d+)$', tableId) is not None:
				tableObj.partitionOf = ossId
			unitObj.addTable(tableId.upper(), tableObj)
			for attr in tableXml.attrib.keys():
				tableObj.add(attr, tableXml.get(attr), 'client')

		for columnXml in tableXml.findall('column'):
			columnId = columnXml.get('id').upper()
			if columnId in tableObj.counters.keys():
				logger.warning(' * [versioningLoader] Duplicated column id \"{:s}\" was found on table \"{:s}\" * '.format(columnId, tableId))
				continue
			columnObj = column()
			columnObj.create(columnId, '', columnXml.get('udn'), columnXml.get('bdcolname'), '', columnXml.get('dbn0type'), columnXml.get('bdtype'), '', '', '', 0)
			if columnObj.dbn0type in ['PK', 'ID']:
				unitObj.addAttribute(columnId, columnObj)
			else:
				tableObj.addCounter(columnId, columnObj)
	return data, matchId, root.attrib['model'], root.attrib['ossversion']

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
						counterObj.add(attr, itemXml.get(attr), 'oss')
					continue

				isMissing = True
				for tableId in tableList.keys():
					tableObj = tableList[tableId]
					if itemId in tableObj.counters.keys():
						isMissing = False
						counterObj = tableObj.counters[itemId]
						for attr in itemXml.attrib.keys():
							counterObj.add(attr, itemXml.get(attr), 'oss')
						break

				if isMissing:
					logger.warning(' * [versioningLoader] itemId \"{:s}\" from ossId \"{:s}\" was not found in client catalog. * '.format(itemId, ossId))
	return data

# #
# Reads and converts operations catalog data to program acceptable data format
# #
def getOperationsStruct(root, data, matchId):
	logger = Logger('processLogger').get()

	for unitXml in root.findall('unit'):
		unitId = unitXml.get('id').upper()

		if unitId in matchId.keys():
			ossId = matchId[unitId].upper()
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
			unitObj.create(unitId, unitId, '', '', '')
			data[unitId] = unitObj
			for opXml in unitXml.findall('operation'):
				unitObj.addOperation('unit', unitId.upper(), opXml)
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

def mergeData(baseData, newData, config):

	for newOssId in newData.keys():
		if newOssId.upper() not in baseData.keys() or newOssId not in baseData.keys():
			baseData[newOssId] = newData[newOssId]
		else:
			newUnitObj = newData[newOssId]
			for baseOssId in baseData.keys():
				if baseOssId == newOssId:
					baseUnitObj = baseData[baseOssId]
					mergeOperations(baseUnitObj, newUnitObj)
					for attr in config['unit'].keys():
						applyConfig(attr.upper(), config['unit'][attr], baseUnitObj, newUnitObj.get(attr))
					for newAttrColumnId in newUnitObj.attributes.keys():
						if newAttrColumnId in baseUnitObj.attributes.keys():
							newAttrColumnObj = newUnitObj.attributes[newAttrColumnId]
							baseAttrColumnObj = baseUnitObj.attributes[newAttrColumnId]
							for attr in config['column'].keys():
								applyConfig(attr.upper(), config['column'][attr], baseAttrColumnObj, newAttrColumnObj.get(attr))

					for newTableId in newUnitObj.tables.keys():
						newTableObj = newUnitObj.tables[newTableId]
						if newTableId in baseUnitObj.tables.keys():
							baseTableObj = baseUnitObj.tables[baseOssId]
							for attr in config['table'].keys():
								applyConfig(attr.upper(), config['table'][attr], baseTableObj, newTableObj.get(attr))
							for newColumnId in newTableObj.counters.keys():
								if newColumnId in baseTableObj.counters.keys():
									newColumnObj = newTableObj.counters[newColumnId]
									baseColumnObj = baseTableObj.counters[newColumnId]
									for attr in config['column'].keys():
										applyConfig(attr.upper(), config['column'][attr], baseColumnObj, newColumnObj.get(attr))
						else:
							baseUnitObj.addTable(newTableId, newTableObj)
							break
	return baseData


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
				if baseObj.get(attr) != '':
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
					if newOpName == baseOpName:
						if newOpName not in operations.keys():
							#logg de erro
							continue

						operations[newOpName].process(baseOpXML, newOpXML)
	pass

# #
# Loads all operations that are configurations in the dir operations
# #
def getOperations():
	operations = dict()
	for importer, packageName, _ in pkgutil.iter_modules(src.merge.xml.operations.__path__):
		operations[packageName] = importer.find_module(packageName).load_module(packageName)
	return operations
