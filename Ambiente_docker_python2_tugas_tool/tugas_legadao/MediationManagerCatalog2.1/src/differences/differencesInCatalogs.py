__doc__ = \
	__version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

from lib.functions import xmlReader, createExcel, createSheet, writeToExcel, writeToSheet
from datetime import datetime
import time
import xml.etree.ElementTree as ET
from lib.Logger import Logger
import pkgutil
from collections import OrderedDict
import src.differences.operations

def process(vendor, collectorConfig, baseCatalogPath, newCatalogPath, shelfCatalogPath, config):
	logger = Logger('differencesInCatalogs').get()
	logger.debug("  ######### START TIME:              {:20s} #########".format(time.strftime("%Y.%m.%d %H:%M:%S")))

	workbook = createExcel()
	deltaClientSheet = createSheet(workbook, 'consolidadoClient')
	getClientDiff(workbook, deltaClientSheet, 'consolidadoClient', baseCatalogPath, newCatalogPath, 'Removed')
	logger.debug("  * [consolidadoClient] Sheet was created *")
	deltaOssSheet = createSheet(workbook, 'consolidadoOss')
	getOssDiff(workbook, deltaOssSheet, 'consolidadoOss', baseCatalogPath, newCatalogPath, 'Removed')
	logger.debug("  * [consolidadoOss] Sheet was created *")

	if shelfCatalogPath != 'sc':
		print shelfCatalogPath
		deltaClientSheet = createSheet(workbook, 'deltaClient')
		getClientDiff(workbook, deltaClientSheet, 'deltaClient', baseCatalogPath, shelfCatalogPath, 'Deprecated')
		logger.debug("  * [deltaClient] Sheet was created *")
		deltaOssSheet = createSheet(workbook, 'deltaOss')
		getOssDiff(workbook, deltaOssSheet, 'deltaOss', baseCatalogPath, shelfCatalogPath, 'Deprecated')
		logger.debug("  * [deltaOss] Sheet was created *")

	writeToExcel(collectorConfig + '_' + str(datetime.now().year) + str(datetime.now().month) + str(datetime.now().day), workbook)
	logger.debug("  ######### END TIME:                {:20s} #########".format(time.strftime("%Y.%m.%d %H:%M:%S")))

# #
# Gets the differences between two client catalogs
# The "missingState" is because the two diff possibles (removed or deprecated)
# #
def getClientDiff(workbook, sheet, sheetName, baseCatalogPath, newCatalogPath,  missingState):

	baseCatalog = xmlReader(baseCatalogPath.replace('#', 'client'))
	newCatalog = xmlReader(newCatalogPath.replace('#', 'client'))

	#Write header
	sheet.write_merge(0, 0, 0, 2, 'Table')
	sheet.write(1, 0, 'id')
	sheet.write(1, 1, 'tableName')
	sheet.write(1, 2, 'udn')
	sheet.write_merge(0, 0, 3, 5, 'Column')
	sheet.write(1, 3, 'id')
	sheet.write(1, 4, 'bdcolname')
	sheet.write(1, 5, 'udn')
	sheet.write_merge(0, 1, 6, 6, 'Attribute')
	baseOssVersion = baseCatalog.get('ossversion')
	sheet.write_merge(0, 1, 7, 7, 'Version ' + baseOssVersion)
	newOssVersion = newCatalog.get('ossversion')
	sheet.write_merge(0, 1, 8, 8, 'Version ' + newOssVersion)
	sheet.write_merge(0, 1, 9, 9, 'State')
	sheet.write_merge(0, 1, 10, 10, 'CaseSensitive')

	sheetRow = 2
	sheetNumber = 1

	# Gets the base catalog data
	baseData = dict()
	for table in baseCatalog.findall('table'):
		tableName = table.get('id').upper()
		if tableName not in baseData.keys():
			baseData[tableName] = dict()
			baseData[tableName]['attributes'] = getElementAttributes(table)
			baseData[tableName]['columns'] = dict()
		for column in table.findall('column'):
			baseData[tableName]['columns'][column.get('id').upper()] = getElementAttributes(column)
	del baseCatalog

	# Gets the new catalog data
	newData = dict()
	for table in newCatalog.findall('table'):
		tableName = table.get('id').upper()
		if tableName not in newData.keys():
			newData[tableName] = dict()
			newData[tableName]['attributes'] = getElementAttributes(table)
			newData[tableName]['columns'] = dict()
		for column in table.findall('column'):
			newData[tableName]['columns'][column.get('id').upper()] = getElementAttributes(column)
	del newCatalog

	# compares new -> old
	for newTable in newData.keys():
		if newTable in baseData.keys():
			for atr in newData[newTable]['attributes'].keys():
				if atr in baseData[newTable]['attributes'].keys():
					if newData[newTable]['attributes'][atr] != baseData[newTable]['attributes'][atr]:
						tmp = [newData[newTable]['attributes']['id'], newData[newTable]['attributes']['tableName'], newData[newTable]['attributes']['udn'], '', '', '', atr, baseData[newTable]['attributes'][atr], newData[newTable]['attributes'][atr], 'Changed Table', ('N' if newData[newTable]['attributes'][atr].upper() != baseData[newTable]['attributes'][atr].upper() else 'Y')]
						writeToSheet(sheet, tmp, sheetRow, 0)
						sheetRow += 1
						sheet, sheetNumber, sheetRow = validateSheetLength(workbook, sheet, sheetName, 'client', sheetNumber, sheetRow, baseOssVersion, newOssVersion)
				else:
					tmp = [newData[newTable]['attributes']['id'], newData[newTable]['attributes']['tableName'], newData[newTable]['attributes']['udn'], '', '', '', atr, '', newData[newTable]['attributes'][atr], 'New Table Tag', '']
					writeToSheet(sheet, tmp, sheetRow, 0)
					sheetRow += 1
					sheet, sheetNumber, sheetRow = validateSheetLength(workbook, sheet, sheetName, 'client', sheetNumber, sheetRow, baseOssVersion, newOssVersion)

			for newColumn in newData[newTable]['columns'].keys():
				if newColumn in baseData[newTable]['columns'].keys():
					for atr in newData[newTable]['columns'][newColumn].keys():
						if atr in baseData[newTable]['columns'][newColumn].keys():
							if newData[newTable]['columns'][newColumn][atr] != baseData[newTable]['columns'][newColumn][atr]:
								tmp = [newData[newTable]['attributes']['id'], newData[newTable]['attributes']['tableName'], newData[newTable]['attributes']['udn'], newData[newTable]['columns'][newColumn]['id'], newData[newTable]['columns'][newColumn]['bdcolname'], newData[newTable]['columns'][newColumn]['udn'], atr, baseData[newTable]['columns'][newColumn][atr], newData[newTable]['columns'][newColumn][atr], 'Changed Column', ('N' if newData[newTable]['columns'][newColumn][atr].upper() != baseData[newTable]['columns'][newColumn][atr].upper() else 'Y')]
								writeToSheet(sheet, tmp, sheetRow, 0)
								sheetRow += 1
								sheet, sheetNumber, sheetRow = validateSheetLength(workbook, sheet, sheetName, 'client', sheetNumber, sheetRow, baseOssVersion, newOssVersion)
						else:
							tmp = [newData[newTable]['attributes']['id'], newData[newTable]['attributes']['tableName'], newData[newTable]['attributes']['udn'], newData[newTable]['columns'][newColumn]['id'], newData[newTable]['columns'][newColumn]['bdcolname'], newData[newTable]['columns'][newColumn]['udn'], atr, '', '', 'New Column Tag', '']
							writeToSheet(sheet, tmp, sheetRow, 0)
							sheetRow += 1
							sheet, sheetNumber, sheetRow = validateSheetLength(workbook, sheet, sheetName, 'client', sheetNumber, sheetRow, baseOssVersion, newOssVersion)
				else:
					tmp = [newData[newTable]['attributes']['id'], newData[newTable]['attributes']['tableName'], newData[newTable]['attributes']['udn'], newData[newTable]['columns'][newColumn]['id'], newData[newTable]['columns'][newColumn]['bdcolname'], newData[newTable]['columns'][newColumn]['udn'], '', '', '', 'New Column', '']
					writeToSheet(sheet, tmp, sheetRow, 0)
					sheetRow += 1
					sheet, sheetNumber, sheetRow = validateSheetLength(workbook, sheet, sheetName, 'client', sheetNumber, sheetRow, baseOssVersion, newOssVersion)
		else:
			counterCount = 0
			for column in newData[newTable]['columns']:
				if 'dbn0type' in newData[newTable]['columns'][column].keys():
					if newData[newTable]['columns'][column]['dbn0type'] in ['MT', 'CM']:
						counterCount += 1
			tmp = [newData[newTable]['attributes']['id'], newData[newTable]['attributes']['tableName'], newData[newTable]['attributes']['udn'], '', '', '', '', '', counterCount, 'New Table', '']
			writeToSheet(sheet, tmp, sheetRow, 0)
			sheetRow += 1
			sheet, sheetNumber, sheetRow = validateSheetLength(workbook, sheet, sheetName, 'client', sheetNumber, sheetRow, baseOssVersion, newOssVersion)

	# Compares old -> new
	for baseTable in baseData.keys():
		if baseTable in newData.keys():
			for atr in baseData[baseTable]['attributes'].keys():
				if atr not in newData[baseTable]['attributes'].keys():
					tmp = [baseData[baseTable]['attributes']['id'], baseData[baseTable]['attributes']['tableName'], baseData[baseTable]['attributes']['udn'], '', '', '', atr, '', '', missingState + ' Table Tag', '']
					writeToSheet(sheet, tmp, sheetRow, 0)
					sheetRow += 1
					sheet, sheetNumber, sheetRow = validateSheetLength(workbook, sheet, sheetName, 'client', sheetNumber, sheetRow, baseOssVersion, newOssVersion)

			for baseColumn in baseData[baseTable]['columns'].keys():
				if baseColumn not in newData[baseTable]['columns'].keys():
					tmp = [baseData[baseTable]['attributes']['id'], baseData[baseTable]['attributes']['tableName'], baseData[baseTable]['attributes']['udn'], baseData[baseTable]['columns'][baseColumn]['id'], baseData[baseTable]['columns'][baseColumn]['bdcolname'], baseData[baseTable]['columns'][baseColumn]['udn'], baseData[baseTable]['columns'][baseColumn]['dbn0type'], '', '', missingState + ' Column', '']
					writeToSheet(sheet, tmp, sheetRow, 0)
					sheetRow += 1
					sheet, sheetNumber, sheetRow = validateSheetLength(workbook, sheet, sheetName, 'client', sheetNumber, sheetRow, baseOssVersion, newOssVersion)
		else:
			tmp = [baseData[baseTable]['attributes']['id'], baseData[baseTable]['attributes']['tableName'], baseData[baseTable]['attributes']['udn'], '', '', '', '', '', len(baseData[baseTable]['columns'].keys()), missingState + ' Table', '']
			writeToSheet(sheet, tmp, sheetRow, 0)
			sheetRow += 1
			sheet, sheetNumber, sheetRow = validateSheetLength(workbook, sheet, sheetName, 'client', sheetNumber, sheetRow, baseOssVersion, newOssVersion)

# #
# Gets the differences between two oss catalogs
# The "missingState" is because the two diff possibles (removed or deprecated)
# #
def getOssDiff(workbook, sheet, sheetName, baseCatalogPath, newCatalogPath,  missingState):

	baseCatalog = xmlReader(baseCatalogPath.replace('#', 'oss'))
	newCatalog = xmlReader(newCatalogPath.replace('#', 'oss'))

	#Write header
	sheet.write_merge(0, 0, 0, 1, 'Unit')
	sheet.write(1, 0, 'id')
	sheet.write(1, 1, 'ossId')
	sheet.write(0, 2, 'Item')
	sheet.write(1, 2, 'id')
	sheet.write_merge(0, 1, 3, 3, 'Attribute')
	baseOssVersion = baseCatalog.get('ossversion')
	sheet.write_merge(0, 1, 4, 4, 'Version ' + baseOssVersion)
	newOssVersion = newCatalog.get('ossversion')
	sheet.write_merge(0, 1, 5, 5, 'Version ' + newOssVersion)
	sheet.write_merge(0, 1, 6, 6, 'State')
	sheet.write_merge(0, 1, 7, 7, 'CaseSensitive')

	sheetRow = 2
	sheetNumber = 1

	# Gets the base catalog data
	baseData = dict()
	for table in baseCatalog.findall('unit'):
		tableName = table.get('id')
		baseData[tableName] = dict()
		baseData[tableName]['attributes'] = getElementAttributes(table)
		baseData[tableName]['item'] = dict()
		for column in table.findall('item'):
			baseData[tableName]['item'][column.get('id')] = getElementAttributes(column)
	del baseCatalog

	# Gets the new catalog data
	newData = dict()
	for table in newCatalog.findall('unit'):
		tableName = table.get('id')
		newData[tableName] = dict()
		newData[tableName]['attributes'] = getElementAttributes(table)
		newData[tableName]['item'] = dict()
		for column in table.findall('item'):
			newData[tableName]['item'][column.get('id')] = getElementAttributes(column)
	del newCatalog

	# Compare new -> old
	for newUnit in newData.keys():
		if newUnit in baseData.keys():
			for atr in newData[newUnit]['attributes'].keys():
				if atr in baseData[newUnit]['attributes'].keys():
					if newData[newUnit]['attributes'][atr] != baseData[newUnit]['attributes'][atr]:
						tmp = [newData[newUnit]['attributes']['id'], newData[newUnit]['attributes']['ossId'], '', atr, baseData[newUnit]['attributes'][atr], newData[newUnit]['attributes'][atr], 'Changed Table', ('N' if newData[newUnit]['attributes'][atr].upper() != baseData[newUnit]['attributes'][atr].upper() else 'Y')]
						writeToSheet(sheet, tmp, sheetRow, 0)
						sheetRow += 1
						sheet, sheetNumber, sheetRow = validateSheetLength(workbook, sheet, sheetName, 'oss', sheetNumber, sheetRow, baseOssVersion, newOssVersion)
				else:
					tmp = [newData[newUnit]['attributes']['id'], newData[newUnit]['attributes']['ossId'], '', atr, '', newData[newUnit]['attributes'][atr], 'New Unit Tag', '']
					writeToSheet(sheet, tmp, sheetRow, 0)
					sheetRow += 1

			for newItem in newData[newUnit]['item'].keys():
				if newItem in baseData[newUnit]['item'].keys():
					for atr in newData[newUnit]['item'][newItem].keys():
						if atr in baseData[newUnit]['item'][newItem].keys():
							if newData[newUnit]['item'][newItem][atr] != baseData[newUnit]['item'][newItem][atr]:
								tmp = [newData[newUnit]['attributes']['id'], newData[newUnit]['attributes']['ossId'], newData[newUnit]['item'][newItem]['id'], atr, baseData[newUnit]['item'][newItem][atr], newData[newUnit]['item'][newItem][atr], 'Changed Item', ('N' if newData[newUnit]['item'][newItem][atr].upper() != baseData[newUnit]['item'][newItem][atr].upper() else 'Y')]
								writeToSheet(sheet, tmp, sheetRow, 0)
								sheetRow += 1
								sheet, sheetNumber, sheetRow = validateSheetLength(workbook, sheet, sheetName, 'oss', sheetNumber, sheetRow, baseOssVersion, newOssVersion)
						else:
							tmp = [newData[newUnit]['attributes']['id'], newData[newUnit]['attributes']['ossId'], newData[newUnit]['item'][newItem]['id'], atr, '', newData[newUnit]['item'][newItem][atr], 'New Item Tag', '']
							writeToSheet(sheet, tmp, sheetRow, 0)
							sheetRow += 1
							sheet, sheetNumber, sheetRow = validateSheetLength(workbook, sheet, sheetName, 'oss', sheetNumber, sheetRow, baseOssVersion, newOssVersion)
				else:
					tmp = [newData[newUnit]['attributes']['id'], newData[newUnit]['attributes']['ossId'], newData[newUnit]['item'][newItem]['id'], '', '', '', 'New Item', '']
					writeToSheet(sheet, tmp, sheetRow, 0)
					sheetRow += 1
					sheet, sheetNumber, sheetRow = validateSheetLength(workbook, sheet, sheetName, 'oss', sheetNumber, sheetRow, baseOssVersion, newOssVersion)
		else:
			tmp = [newData[newUnit]['attributes']['id'], newData[newUnit]['attributes']['ossId'], '', '', '', '', 'New Unit', '']
			writeToSheet(sheet, tmp, sheetRow, 0)
			sheetRow += 1

	# Compare old -> new
	for baseUnit in baseData.keys():
		if baseUnit in newData.keys():
			for atr in baseData[baseUnit]['attributes'].keys():
				if atr not in newData[baseUnit]['attributes'].keys():
					tmp = [baseData[baseUnit]['attributes']['id'], baseData[baseUnit]['attributes']['ossId'], '', atr, '', '', missingState + ' Unit Attribute', '']
					writeToSheet(sheet, tmp, sheetRow, 0)
					sheetRow += 1
					sheet, sheetNumber, sheetRow = validateSheetLength(workbook, sheet, sheetName, 'oss', sheetNumber, sheetRow, baseOssVersion, newOssVersion)

			for baseItem in baseData[baseUnit]['item'].keys():
				if baseItem not in newData[baseUnit]['item'].keys():
					tmp = [baseData[baseUnit]['attributes']['id'], baseData[baseUnit]['attributes']['ossId'], baseData[baseUnit]['item'][baseItem]['id'], '', '', '', missingState + ' Item', '']
					writeToSheet(sheet, tmp, sheetRow, 0)
					sheetRow += 1
					sheet, sheetNumber, sheetRow = validateSheetLength(workbook, sheet, sheetName, 'oss', sheetNumber, sheetRow, baseOssVersion, newOssVersion)
		else:
			tmp = [baseData[baseUnit]['attributes']['id'], baseData[baseUnit]['attributes']['ossId'], '', '', '', '', missingState + ' Unit', '']
			writeToSheet(sheet, tmp, sheetRow, 0)
			sheetRow += 1
			sheet, sheetNumber, sheetRow = validateSheetLength(workbook, sheet, sheetName, 'oss', sheetNumber, sheetRow, baseOssVersion, newOssVersion)

# #
# Gets the differences between two operations catalogs
# The "missingState" is because the two diff possibles (removed or deprecated)
# #
def getOperationsDiff(workbook, sheet, sheetName, baseCatalogPath, newCatalogPath,  missingState):

	baseCatalog = xmlReader(baseCatalogPath.replace('#', 'operations'))
	newCatalog = xmlReader(newCatalogPath.replace('#', 'operations'))

	#Write header
	sheet.write_merge(0, 0, 0, 1, 'Unit')
	sheet.write(1, 0, 'id')
	sheet.write(0, 1, 'Item')
	sheet.write(1, 1, 'id')
	sheet.write_merge(0, 1, 2, 2, 'Operation')
	baseOssVersion = baseCatalog.get('ossversion')
	sheet.write_merge(0, 1, 3, 3, 'Version ' + baseOssVersion)
	newOssVersion = newCatalog.get('ossversion')
	sheet.write_merge(0, 1, 4, 4, 'Version ' + newOssVersion)
	sheet.write_merge(0, 1, 5, 5, 'State')

	sheetRow = 2
	sheetNumber = 1

	# Gets the base catalog data
	baseData = dict()
	for unit in baseCatalog.findall('unit'):
		unitId = unit.get('id').upper()
		if unitId in baseData.keys():
			print 'UNIT DUPLICADA'
		baseData[unitId] = dict()
		baseData[unitId]['operation'] = dict()
		for operation in unit.findall('operation'):
			opType = operation.get('type')
			if opType not in baseData[unitId]['operation'].keys():
				baseData[unitId]['operation'][opType] = list()
			if ET.tostring(operation) in baseData[unitId]['operation'][opType]:
				print 'OPERACAO UNIT DUPLICADA'
				continue
			baseData[unitId]['operation'][opType].append(ET.tostring(operation))

		baseData[unitId]['item'] = dict()
		for item in unit.findall('item'):
			itemId = item.get('id').upper()
			if itemId in baseData[unitId]['item'].keys():
				print 'ITEM DUPLICADO'
			baseData[unitId]['item'][item.get('id')][itemId] = dict()

			for operation in item.findall('operation'):
				opType = operation.get('type')
				if opType not in baseData[unitId]['item'][itemId].keys():
					baseData[unitId]['item'][itemId][opType] = list()
				if ET.tostring(operation) in baseData[unitId]['item'][itemId][opType]:
					print 'OPERACAO ITEM DUPLICADA'
					continue
				baseData[unitId]['item'][itemId][opType].append(ET.tostring(operation))
	del baseCatalog

	# Gets the new catalog data
	newData = dict()
	for unit in newCatalog.findall('unit'):
		unitId = unit.get('id').upper()
		if unitId in newData.keys():
			print 'UNIT DUPLICADA'
		newData[unitId] = dict()
		newData[unitId]['operation'] = dict()
		for operation in unit.findall('operation'):
			opType = operation.get('type')
			if opType not in newData[unitId]['operation'].keys():
				newData[unitId]['operation'][opType] = list()
			if ET.tostring(operation) in newData[unitId]['operation'][opType]:
				print 'OPERACAO UNIT DUPLICADA'
				continue
			newData[unitId]['operation'][opType].append(ET.tostring(operation))

		newData[unitId]['item'] = dict()
		for item in unit.findall('item'):
			itemId = item.get('id').upper()
			if itemId in newData[unitId]['item'].keys():
				print 'ITEM DUPLICADO'
			newData[unitId]['item'][item.get('id')][itemId] = dict()

			for operation in item.findall('operation'):
				opType = operation.get('type')
				if opType not in newData[unitId]['item'][itemId].keys():
					newData[unitId]['item'][itemId][opType] = list()
				if ET.tostring(operation) in newData[unitId]['item'][itemId][opType]:
					print 'OPERACAO ITEM DUPLICADA'
					continue
				newData[unitId]['item'][itemId][opType].append(ET.tostring(operation))
	del newCatalog

	operationsList = getOperations()

	for unitId in newData.keys():
		if unitId in baseData.keys():
			for operation in newData[unitId]['operation'].keys():
				if operation in baseData[unitId]['operation'].keys():
					if operation not in operationsList.keys():
						operationsList[operation].process(sheet, baseData[unitId]['operation'][operation], newData[unitId]['operation'][operation])


	for unitId in baseData.keys():
		if unitId in newData.keys():
			for operation in baseData[unitId]['operation'].keys():
				if operation in newData[unitId]['operation'].keys():
					if operation not in operationsList.keys():
						operationsList[operation].process(sheet, baseData[unitId]['operation'][operation], newData[unitId]['operation'][operation])
	#DONE UNTIL HERE



# #
# For retrieving all tags and its values from an element
# #
def getElementAttributes(bElement):
	data = dict()
	for atr in bElement.attrib:
		data[atr] = bElement.get(atr)
	return data

# #
# Validates if the sheet has reached the limit number of lines (aprox. 65000)
# And if the sheet has reached the limit creates a new one
# #
def validateSheetLength(workbook, sheet, sheetName, sheetType, sheetNumber, sheetRow, baseOssVersion, newOssVersion):

	if sheetRow >= 65000:
		sheet = createSheet(workbook, sheetName + '_' + str(sheetNumber))
		sheetNumber += 1
		if sheetType == 'client':
			sheet.write_merge(0, 0, 0, 2, 'Table')
			sheet.write(1, 0, 'id')
			sheet.write(1, 1, 'tableName')
			sheet.write(1, 2, 'udn')
			sheet.write_merge(0, 0, 3, 5, 'Column')
			sheet.write(1, 3, 'id')
			sheet.write(1, 4, 'bdcolname')
			sheet.write(1, 5, 'udn')
			sheet.write_merge(0, 1, 6, 6, 'Attribute')
			sheet.write_merge(0, 1, 7, 7, 'Version ' + baseOssVersion)
			sheet.write_merge(0, 1, 8, 8, 'Version ' + newOssVersion)
			sheet.write_merge(0, 1, 9, 9, 'State')
			sheet.write_merge(0, 1, 10, 10, 'CaseSensitive')
		elif sheetType == 'oss':
			sheet.write_merge(0, 0, 0, 1, 'Unit')
			sheet.write(1, 0, 'id')
			sheet.write(1, 1, 'ossId')
			sheet.write(0, 2, 'Item')
			sheet.write(1, 2, 'id')
			sheet.write_merge(0, 1, 3, 3, 'Attribute')
			sheet.write_merge(0, 1, 4, 4, 'Version ' + baseOssVersion)
			sheet.write_merge(0, 1, 5, 5, 'Version ' + newOssVersion)
			sheet.write_merge(0, 1, 6, 6, 'State')
			sheet.write_merge(0, 1, 7, 7, 'CaseSensitive')
		sheetRow = 2

	return sheet, sheetNumber, sheetRow


def getOperations():
	operationsList = OrderedDict()
	for importer, packageName, xx in pkgutil.iter_modules(src.differences.operations.__path__):
		operationsList[packageName] = dict()
		operationsList[packageName] = importer.find_module(packageName).load_module(packageName)
	return operationsList