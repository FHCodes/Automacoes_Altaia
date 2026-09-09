__doc__ = \
	__version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

from src.inputFormats.generic.excelBase import excelBase
from lib.objects.column import column
from lib.objects.table import table
from lib.objects.unit import unit
from lib.functions import validateInformation
import json
import re
from lib.Logger import Logger

# #
# Nokia/NSN excel data processor
# #
def process(docPath, fileConfigName, dataConfig, vendor):
	logger = Logger('processLogger').get()
	catalogType = dataConfig['collector']['collectorType']
	fileConfig = json.load(open('./config/inputConfigs/' + fileConfigName+'.json'))

	info = excelBase(docPath, fileConfig, catalogType).getExcelInfo()

	if catalogType == "PM":
		info = transformPerformance(info)
	# Configurations to be applied if catalog type is CM (Parameters)
	#if catalogType == 'CM':
	#	transformParameters(info)

	# Validates the consistency of the data
	validateInformation(info, catalogType, vendor, dataConfig['rules'])

	data = dict()

	for tableId in info.keys():
		tableInfo = info[tableId]['attributes']
		unitOssId = tableInfo['ossId']

		tableObj = table()
		tableObj.create(tableInfo['id'].upper(), tableInfo['ossId'].upper(), tableInfo['tableName'].upper(), tableInfo['udn'])
		tableObj.tech = dataConfig['collector']['tech']

		if unitOssId not in data.keys():
			unitObj = unit()
			unitObj.create(unitOssId.upper(), tableInfo['id'].upper(), tableInfo['name'], tableInfo['desc'], tableInfo['hierarchy'])
			data[unitOssId] = unitObj
		else:
			unitObj = data[unitOssId]

		if tableId in unitObj.tables.keys():
			tableObj = unitObj.getTable(tableId)
		else:
			unitObj.addTable(tableId, tableObj)

		for columnId in info[tableId]['items'].keys():
			columnInfo = info[tableId]['items'][columnId]
			columnInfo['id'] = re.sub(r'\<|\>', '', columnInfo['id'].upper())
			if columnInfo['id'] in tableObj.counters.keys() or columnInfo['id'] in unitObj.attributes.keys():
				logger.warning(' * Duplicated column id \"{:s}\" in table \"{:s}\", new information was discarted * '.format(columnId, tableId))
				continue

			columnObj = column()
			columnObj.create(columnInfo['id'], re.sub(r'\<|\>', '', columnInfo['name'].upper()), re.sub(r'\<|\>', '', columnInfo['udn']), re.sub(r'\<|\>', '', columnInfo['bdcolname'].upper()), re.sub(r'\<|\>', '', columnInfo['desc'].upper()), columnInfo['dbn0type'], columnInfo['bdtype'], columnInfo['typeCust'], columnInfo['dataType'], columnInfo['dataUnit'], columnInfo['multiplicity'])

			if columnObj.dbn0type in ['PK', 'ID']:
				unitObj.addAttribute(columnInfo['id'], columnObj)
			else:
				tableObj.addCounter(columnInfo['id'], columnObj)


	return data


def transformPerformance(info):
	for tableId in info.keys():
		listToRemove = list()
		for columnId in info[tableId]['items'].keys():
			if 'ZTEMPORARY' in columnId.upper():
				listToRemove.append(columnId)
				continue
			columnInfo = info[tableId]['items'][columnId]
			if tableId.upper() == 'EUTRANCELLTDD':
				if columnInfo['multiplicity'].upper() not in ['', 'SINGLE'] or columnInfo['dataType'].upper() in ['DDM', 'PDF']:
					listToRemove.append(columnId)
					continue
			if columnInfo['multiplicity'].upper() == 'SINGLE':
				columnInfo['multiplicity'] = ""
			else:
				columnInfo['multiplicity'] = re.sub(r'\[|\]|\s', '', columnInfo['multiplicity'])

		for columnId in listToRemove:
			del info[tableId]['items'][columnId]
	return info

def transformParameters(info):
	unitList = dict()
	dependencies = dict()
	disableHierarchyList = list()
	for unitKey in info.keys():
		if info[unitKey]['attributes']['father'] == info[unitKey]['attributes']['id'] and info[unitKey]['attributes']['father'] not in unitList.keys() and info[unitKey]['attributes']['isStruct'] not in ['True', True]:
			unitList[info[unitKey]['attributes']['ossId']] = info[unitKey]['attributes']['hierarchy']
		if info[unitKey]['attributes']['isStruct'] in ['True', True] and info[unitKey]['attributes']['Origin'] not in dependencies.keys():
			dependencies[info[unitKey]['attributes']['Origin']] = list()

	for unitKey in info.keys():
		if info[unitKey]['attributes']['father'] != info[unitKey]['attributes']['id']:
			if info[info[unitKey]['attributes']['Origin'].upper()]['attributes']['hierarchy'] == '':
				info[info[unitKey]['attributes']['Origin'].upper()]['attributes']['hierarchy'] = unitList[info[unitKey]['attributes']['father']] + '-' + info[unitKey]['attributes']['Origin']
			else:
				info[info[unitKey]['attributes']['Origin'].upper()]['attributes']['hierarchy'] += ', ' + unitList[info[unitKey]['attributes']['father']] + '-' + info[unitKey]['attributes']['Origin']
			dependencies[info[unitKey]['attributes']['Origin']].append(info[unitKey]['attributes']['id'])

	for unitKey in info.keys():
		if info[unitKey]['attributes']['father'] != info[unitKey]['attributes']['id']:
			if info[unitKey]['attributes']['hierarchy'] == '':
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
					if info[isSon]['attributes']['hierarchy'] is '':
						info[isSon]['attributes']['hierarchy'] = info[isFather]['attributes']['hierarchy'] + '-' + isSon
					else:
						info[isSon]['attributes']['hierarchy'] += ',' + info[isFather]['attributes']['hierarchy'] + '-' + isSon

					info[isSon]['attributes']['dependencies'].append(unitKey)

				if info[unitKey]['attributes']['hierarchy'] is '':
					info[unitKey]['attributes']['hierarchy'] = info[isFather]['attributes']['hierarchy'] + '-' + isSon
					info[unitKey]['attributes']['disableHierarchy'] = "True"
				else:
					info[unitKey]['attributes']['hierarchy'] += ',' + info[isFather]['attributes']['hierarchy'] + '-' + isSon
	return info