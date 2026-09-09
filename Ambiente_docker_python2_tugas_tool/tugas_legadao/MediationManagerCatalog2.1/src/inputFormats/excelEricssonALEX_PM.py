__doc__ = \
	__version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

from src.inputFormats.generic.excelBase import excelBase
from lib.objects.column import column
from lib.objects.table import table
from lib.objects.unit import unit
from src.inputFormats.alexFormat import readAlexFile
from lib.functions import validateInformation
import re
import math
import json
from lib.Logger import Logger
from collections import OrderedDict

# #
# Ericsson excel and alex data processor
# #
def process(docPath, fileConfigName, dataConfig, vendor):
	logger = Logger('processLogger').get()
	catalogType = dataConfig['collector']['collectorType']
	fileConfig = json.load(open('./config/inputConfigs/' + fileConfigName+'.json'), object_pairs_hook=OrderedDict)

	# If data is not an excel, them process data as alex (path of excelEricssonALEX.pythe unzip dir of the alex)
	if '.xls' not in docPath:
		docPath = readAlexFile(docPath)

	info = excelBase(docPath, fileConfig, catalogType).getExcelInfo()
	#structList = list()
	dependencies = dict()
	disableHierarchyList = list()
	if catalogType == 'CM':
		info, dependencies, disableHierarchyList = transformParameters(info)

	validateInformation(info, catalogType, vendor, dataConfig['rules'])

	data = dict()
	
	for tableId in info.keys():
		tableInfo = info[tableId]['attributes']
		unitOssId = tableInfo['ossId']

		tableObj = table()
		tableObj.create(tableInfo['id'], tableInfo['ossId'], tableInfo['tableName'], tableInfo['udn'])

		if unitOssId not in data.keys():
			unitObj = unit()
			unitObj.create(unitOssId, tableInfo['id'], tableInfo['name'], tableInfo['desc'].strip(), tableInfo['hierarchy'])
			data[unitOssId] = unitObj
		else:
			unitObj = data[unitOssId]

		if tableId in disableHierarchyList:
			unitObj.disableHierarchy()

		if tableInfo['id'] in unitObj.tables.keys():
			tableObj = unitObj.getTable(tableInfo['id'])
		else:
			unitObj.addTable(tableInfo['id'], tableObj)

		try:
			for dep in dependencies[tableInfo['ossId']]:
				unitObj.addStructDependencie(dep)
		except:
			pass

		if tableInfo['hierarchy'] == '':
			unitObj.disableHierarchy()

		for columnId in info[tableId]['items'].keys():
			if 'ZTEMPORARY' in columnId.upper() or (unitOssId.upper() == 'EUTRANCELLTDD' and columnInfo['multiplicity'] not in ['', 'SINGLE', 0, '0']):
				continue
			columnInfo = info[tableId]['items'][columnId]

			if columnInfo['dataUnit'].upper() not in ['PDF', 'DDM'] and columnInfo['multiplicity'] == '':
				columnInfo['multiplicity'] = 0

			if columnInfo['id'] in tableObj.counters.keys() or columnInfo['id'] in unitObj.attributes.keys():
				logger.warning(' * Duplicated column id \"{:s}\" in table \"{:s}\", new information was discarted * '.format(columnId, tableId))
				continue

			columnObj = column()
			columnObj.create(columnInfo['id'], columnInfo['name'], columnInfo['udn'], columnInfo['bdcolname'], columnInfo['desc'].strip(), columnInfo['dbn0type'], columnInfo['bdtype'], columnInfo['typeCust'], columnInfo['dataType'], columnInfo['dataUnit'], columnInfo['multiplicity'])

			if 'COMPRESSED:TRUE' in re.sub(r'((\n)|(\r)| )', '', columnInfo['desc'].upper()):
				columnObj.compressed = 'True'

			if columnObj.dbn0type in ['PK', 'ID']:
				unitObj.addAttribute(columnInfo['id'], columnObj)
			else:
				tableObj.addCounter(columnInfo['id'], columnObj)

	#if catalogType == 'CM':
	#	transformParametersAfter(unitData, info.keys())

	#if catalogType == 'PM':
	#	transformPerformanceAfter(unitData)

	return data

def transformParameters(info):
	unitList = dict()
	dependencies = dict()
	disableHierarchyList = list()
	for unitKey in info.keys():
		if info[unitKey]['attributes']['hierarchy'].replace(',','') == '':
			info[unitKey]['attributes']['hierarchy'] = ''
		if info[unitKey]['attributes']['father'] == info[unitKey]['attributes']['id'] and info[unitKey]['attributes']['father'] not in unitList.keys() and info[unitKey]['attributes']['isStruct'] not in ['True', True]:
			unitList[info[unitKey]['attributes']['ossId']] = info[unitKey]['attributes']['hierarchy']
		if info[unitKey]['attributes']['isStruct'] in ['True', True] and info[unitKey]['attributes']['Origin'] not in dependencies.keys():
			dependencies[info[unitKey]['attributes']['Origin']] = list()

	for unitKey in info.keys():
		if info[unitKey]['attributes']['father'] != info[unitKey]['attributes']['id']:
			if info[info[unitKey]['attributes']['Origin'].upper()]['attributes']['hierarchy'] in ['', ' ', ',', ', ']:
				info[info[unitKey]['attributes']['Origin'].upper()]['attributes']['hierarchy'] = unitList[info[unitKey]['attributes']['father']] + '-' + info[unitKey]['attributes']['Origin']
			else:
				info[info[unitKey]['attributes']['Origin'].upper()]['attributes']['hierarchy'] += ', ' + unitList[info[unitKey]['attributes']['father']] + '-' + info[unitKey]['attributes']['Origin']

			dependencies[info[unitKey]['attributes']['Origin']].append(info[unitKey]['attributes']['id'])

	for unitKey in info.keys():
		if info[unitKey]['attributes']['father'] != info[unitKey]['attributes']['id']:
			if info[unitKey]['attributes']['hierarchy'] in ['', ' ', ',', ', ']:
				info[unitKey]['attributes']['hierarchy'] = unitList[info[unitKey]['attributes']['father']] + '-' + info[unitKey]['attributes']['Origin']
			else:
				info[unitKey]['attributes']['hierarchy'] += ', ' + unitList[info[unitKey]['attributes']['father']] + '-' + info[unitKey]['attributes']['Origin']
			disableHierarchyList.append(unitKey)
			pass
	return info, dependencies, disableHierarchyList

	unitList = info.keys()
	for unitKey in unitList:
		if '_' in info[unitKey]['attributes']['id']:
			isFather = info[unitKey]['attributes']['id'].split('_')[0]
			isSon = info[unitKey]['attributes']['id'].replace(isFather + '_', '')

			if isFather in unitList:
				if isSon in unitList:
					if 'dependencies' not in info[isSon]['attributes'].keys():
						info[isSon]['attributes']['dependencies'] = list()
					if info[isSon]['attributes']['hierarchy'] in ['', ' ', ',', ', ']:
						info[isSon]['attributes']['hierarchy'] = info[isFather]['attributes']['hierarchy'] + '-' + isSon
					else:
						info[isSon]['attributes']['hierarchy'] += ',' + info[isFather]['attributes']['hierarchy'] + '-' + isSon

					info[isSon]['attributes']['dependencies'].append(unitKey)

				if info[unitKey]['attributes']['hierarchy'] in ['', ' ', ',', ', ']:
					info[unitKey]['attributes']['hierarchy'] = info[isFather]['attributes']['hierarchy'] + '-' + isSon
					info[unitKey]['attributes']['disableHierarchy'] = "True"
				else:
					info[unitKey]['attributes']['hierarchy'] += ',' + info[isFather]['attributes']['hierarchy'] + '-' + isSon
	return info

def transformPerformance(info):
	unitList = info['items'].keys()
	unitIndex = dict()
	for unitKey in unitList:
		i = len(info['item'][unitKey])-1
		while i >= 0:
			itemKey = info['item'][unitKey][i]
			if itemKey['multiplicity'] is not '':
				if unitKey not in unitIndex.keys():
					unitIndex[unitKey] = 1
					
				isSon = unitKey + '_' + itemKey['id']
				isSonId = unitKey + '_' + str(unitIndex[unitKey])
				if isSonId not in unitList:
					info['unit'][isSonId] = dict(info['unit'][unitKey])
					info['unit'][isSonId]['udn'] = isSon
					info['unit'][isSonId]['id'] = isSonId
					info['unit'][isSonId]['sqlName'] = isSonId
					unitIndex[unitKey] += 1
					info['item'][isSonId] = list()
					info['item'][isSonId].append(itemKey)
					del info['item'][unitKey][i]

					for index in range(0, int(itemKey['multiplicity'])):
						tmp = dict()
						tmp['id'] = itemKey['id'] + 'Sub' + str(index)
						tmp['name'] = tmp['id']
						tmp['udn'] = tmp['id']
						tmp['bdcolname'] = tmp['id']
						tmp['desc'] = tmp['id']
						tmp['dataType'] = itemKey['dataType']
						tmp['dataUnit'] = itemKey['dataUnit']
						tmp['multiplicity'] = ''
						info['item'][isSonId].append(tmp)
			i -= 1
	return info

def transformPerformanceAfter(unitData):
	while unitData is not None:
		position = int(math.floor(int(unitData.size)/950) + 1)
		itemData = unitData.items
		while itemData is not None:
			if itemData.multiplicity not in ['', 0]:
				newUnit = unit()
				prevItem = itemData.getPrev()
				nextItem = itemData.getNext()
				if prevItem is not None:
					prevItem.setNext(nextItem)
				if nextItem is not None:
					nextItem.setPrev(prevItem)
				typeId = unitData.ossId + '_' + str(position)
				newUnit.create(typeId, unitData.ossId, unitData.name, typeId, unitData.ossId + '_' + itemData.typeId, unitData.desc, unitData.measuredObject + '-' + itemData.typeId, itemData, 1)

				itemData.setPrev(None)
				for i in range(0, int(itemData.multiplicity)):
					newItem = column()
					typeId = itemData.typeId + 'Sub' + str(i)
					newItem.create(typeId, typeId, typeId, typeId, itemData.desc + ' [' + str(i) + ']', 'MT', itemData.bdtype, itemData.typeCust, itemData.typeVendor, '', 'Single')
					itemData.setNext(newItem)
					newItem.setPrev((itemData))
					itemData = newItem

				itemData = newUnit.items
				itemData.bdtype = 'VARCHAR2(256)'
				itemData.dbn0type = 'MT'
				itemData.typeCust = 'STRING'
				itemData.typeVendor = 'STRING'
				itemData.unitVendor = 'PDF'

				nextUnit = unitData.getNext()
				#need's work
				if nextUnit is not None:
					if nextUnit.ossId is unitData.ossId:
						afterNextUnit = nextUnit.getNext()
						nextUnit.setNext(newUnit)
						newUnit.setPrev(nextUnit)
						newUnit.setNext(afterNextUnit)
						if afterNextUnit is not None:
							afterNextUnit.setPrev(newUnit)
					else:
						unitData.setNext(newUnit)
						newUnit.setPrev(unitData)
						newUnit.setNext(nextUnit)
						if nextUnit is not None:
							nextUnit.setPrev(newUnit)
				else:
					unitData.setNext(newUnit)

				position += 1
				itemData = nextItem
			else:
				itemData = itemData.getNext()

		while unitData.getNext() is not None:
			if unitData.ossId != unitData.getNext().ossId:
				break
			unitData = unitData.getNext()
		unitData = unitData.getNext()

