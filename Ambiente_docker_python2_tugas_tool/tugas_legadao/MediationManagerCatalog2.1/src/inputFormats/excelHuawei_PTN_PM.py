__doc__ = \
	__version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

from src.inputFormats.generic.excelBase import excelBase
from lib.objects.column import column
from lib.objects.table import table
from lib.objects.unit import unit
from lib.functions import validateInformation
import re
import json
from collections import OrderedDict
from lib.Logger import Logger

# #
# Huawei excel data processor
# #
def process(docPath, fileConfigName, dataConfig, vendor):
	catalogType = dataConfig['collector']['collectorType']
	fileConfig = json.load(open('./config/inputConfigs/' + fileConfigName+'.json'), object_pairs_hook=OrderedDict)

	info = excelBase(docPath, fileConfig, catalogType).getExcelInfo()

	info = validateInformation(info, catalogType, vendor, dataConfig['rules'])

	data = dict()

	for tableId in info.keys():

		tableInfo = info[tableId]['attributes']
		unitOssId = tableInfo['ossId']

		tableObj = table()
		tableObj.create(tableInfo['id'], tableInfo['ossId'], tableInfo['tableName'], tableInfo['udn'])

		if unitOssId not in data.keys():
			unitObj = unit()
			unitObj.create(unitOssId, tableInfo['id'], tableInfo['name'], tableInfo['desc'], tableInfo['hierarchy'])
			data[unitOssId] = unitObj
		else:
			unitObj = data[unitOssId]

		for attr in tableInfo.keys():
			if attr not in ['id', 'ossId', 'name', 'udn', 'desc', 'tableName', 'hierarchy', 'tech', 'disableHierarchy']:
				unitObj.addExtra('client', attr, tableInfo[attr])
				unitObj.addExtra('oss', attr, tableInfo[attr])

		if tableInfo['id'] in unitObj.tables.keys():
			tableObj = unitObj.getTable(tableInfo['id'])
		else:
			unitObj.addTable(tableInfo['id'], tableObj)

		for columnId in info[tableId]['items'].keys():
			columnInfo = info[tableId]['items'][columnId]
			columnInfo['desc'] = re.sub(r'&.+?;', '', columnInfo['desc'])
			if columnInfo['desc'].startswith(' '):
				columnInfo['desc'] = columnInfo['desc'][1:]
			if columnInfo['desc'].endswith(' '):
				columnInfo['desc'] = columnInfo['desc'][:-1]

			#equipment = ''
			#for attr in columnInfo.keys():
			#	if attr in ['OSN1800V', 'OSN500', 'OSN550', 'OSN7500', 'OSN9800U32']:
			#		if equipment != '' and columnInfo[attr] == 'Y':
			#			equipment = equipment + ';' + attr
			#		elif columnInfo[attr] == 'Y':
			#			equipment = attr
			#		del columnInfo[attr]
			#columnInfo['equipment'] = equipment
			#if equipment == '':
			#	continue

			columnObj = column()
			columnObj.create(columnInfo['id'], re.sub(r'\<|\>|&', '', columnInfo['name']), re.sub(r'\<|\>', '', columnInfo['udn']), re.sub(r'\<|\>', '', columnInfo['bdcolname']), re.sub(r'\<|\>', '', columnInfo['desc']), columnInfo['dbn0type'], columnInfo['bdtype'], columnInfo['typeCust'], columnInfo['dataType'], columnInfo['dataUnit'], columnInfo['multiplicity'])
			for attr in columnInfo.keys():
				if attr not in ['id', 'ossId', 'bdcolname', 'name', 'udn', 'desc', 'dbn0type', 'bdtype', 'dataType', 'dataUnit', 'multiplicity']:
					columnObj.addExtra('oss', attr, columnInfo[attr])

			if columnObj.dbn0type in ['PK', 'ID']:
				unitObj.addAttribute(columnInfo['id'], columnObj)
			else:
				tableObj.addCounter(columnInfo['id'], columnObj)

	return data
