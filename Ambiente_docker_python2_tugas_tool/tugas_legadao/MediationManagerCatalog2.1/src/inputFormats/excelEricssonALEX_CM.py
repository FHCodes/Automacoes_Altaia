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
import xml.etree.ElementTree as ET

# #
# Ericsson excel and alex data processor
# #
def process(docPath, fileConfigName, dataConfig, vendor):
	arrayNumberRegex = re.compile(r'^.*\[\d+\.\.(?P<num>\d+)\].*$')
	intRegex = re.compile(r'((U)?INT\d+).*$')
	logger = Logger('processLogger').get()
	catalogType = dataConfig['collector']['collectorType']
	fileConfig = json.load(open('./config/inputConfigs/' + fileConfigName+'.json'), object_pairs_hook=OrderedDict)

	# If data is not an excel, them process data as alex (path of excelEricssonALEX.pythe unzip dir of the alex)
	if '.xls' not in docPath:
		docPath = readAlexFile(docPath)

	info = excelBase(docPath, fileConfig, catalogType).getExcelInfo()

	structList = getStructs(info)
	enumList = getEnums(info)

	dependencies = dict()
	disableHierarchyList = list()
	#if catalogType == 'CM':
	#	info, dependencies, disableHierarchyList = transformParameters(info)

	validateInformation(info, catalogType, vendor, dataConfig['rules'], enumList)

	data = dict()
	
	for tableId in info.keys():
		tableInfo = info[tableId]['attributes']
		unitOssId = tableInfo['ossId'].upper()
		try:
			if tableInfo['isStruct'] == 'True' or tableInfo['isEnum'] == 'True':
				continue
		except KeyError:
			pass

		tableObj = table()
		tableObj.create(tableInfo['id'], tableInfo['ossId'], tableInfo['tableName'], tableInfo['udn'])

		if unitOssId not in data.keys():
			unitObj = unit()
			unitObj.create(unitOssId, tableInfo['id'].upper(), tableInfo['name'], tableInfo['desc'].strip(), tableInfo['hierarchy'])
			data[unitOssId] = unitObj
		else:
			unitObj = data[unitOssId]

		if tableId in disableHierarchyList:
			unitObj.disableHierarchy()

		if tableInfo['id'].upper() in unitObj.tables.keys():
			tableObj = unitObj.getTable(tableInfo['id'].upper())
		else:
			unitObj.addTable(tableInfo['id'].upper(), tableObj)

		try:
			for dep in dependencies[tableInfo['ossId']]:
				unitObj.addStructDependencie(dep)
		except:
			pass

		if tableInfo['hierarchy'] == '':
			unitObj.disableHierarchy()

		for columnId in info[tableId]['items'].keys():
			if 'ZTEMPORARY' in columnId.upper() or (unitOssId.upper() == 'EUTRANCELLTDD_XYZ' and columnInfo['multiplicity'] not in ['', 'SINGLE']):
				continue
			columnInfo = info[tableId]['items'][columnId]

			if columnInfo['dataType'].upper() in structList:
				createSubFamily(columnInfo['id'], tableInfo, structList[columnInfo['dataType'].upper()], data)
				continue

			try:
				if columnInfo['isStruct'] == 'True':
					continue
			except KeyError:
				pass

			if columnInfo['dataUnit'].upper() not in ['PDF', 'DDM'] and columnInfo['multiplicity'] == '':
				columnInfo['multiplicity'] = 0

			if columnInfo['id'] in tableObj.counters.keys() or columnInfo['id'] in unitObj.attributes.keys():
				logger.warning(' * Duplicated column id \"{:s}\" in table \"{:s}\", new information was discarted * '.format(columnId, tableId))
				continue

			if '[' in columnInfo['dataType']:
				tmp = columnInfo['dataType'].split('[')
				# columnInfo['dataType'] = tmp[0]
				tmp = tmp[1].split(']')
				if tmp[0] not in ['0..1', '..1']:
					columnInfo['bdtype'] = 'VARCHAR2(600)'
					columnInfo['typeCust'] = 'STRING'

			columnObj = column()
			columnObj.create(columnInfo['id'].upper(), columnInfo['name'], columnInfo['udn'], columnInfo['bdcolname'].upper(), columnInfo['desc'].strip(), columnInfo['dbn0type'], columnInfo['bdtype'], columnInfo['typeCust'], columnInfo['dataType'], columnInfo['dataUnit'], columnInfo['multiplicity'])

			if 'COMPRESSED:TRUE' in re.sub(r'((\n)|(\r)| )', '', columnInfo['desc'].upper()):
				columnObj.compressed = 'True'

			if columnObj.dbn0type in ['PK', 'ID']:
				unitObj.addAttribute(columnInfo['id'].upper(), columnObj)
			else:
				tableObj.addCounter(columnInfo['id'].upper(), columnObj)

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

def createSubFamily(field, parent, struct, data):
	name = '{0}_{1}'.format(parent['ossId'], field)
	familyId = name.upper()

	hierarchy = ''
	splitChar = ''
	for measObj in parent['hierarchy'].split(','):
		hierarchy = '{0}{1}{2}-{3}'.format(hierarchy, splitChar, measObj, field)
		splitChar = ','

	if field.upper() not in data.keys():
		unitObj = unit()
		unitObj.create(field.upper(), field.upper(), field, field, hierarchy)
		unitObj.setDummy()
		data[field.upper()] = unitObj

		eOperation = ET.Element('operation')
		eOperation.set('type', 'unitSplitv2')

		fieldSplit = ET.SubElement(eOperation, 'field')
		fieldSplit.set('id', 'FDN')

		regex = ET.SubElement(fieldSplit, 'regex')
		regex.set('pattern', '.*{0}=.+,{1}=.+$'.format(parent['name'], field))
		regex.set('newunit', familyId)
		unitObj.addOperation('unit', 'unitSplitv2', eOperation)
	else:
		unitObj = data[field.upper()]
		unitObj.measuredObject = '{0},{1}'.format(unitObj.measuredObject, hierarchy)

		for eOperation in unitObj.getOperation('unit', 'unitSplitv2'):
			fieldSplit = eOperation.find('field')
			if fieldSplit.get('id') == 'FDN':
				regex = ET.SubElement(fieldSplit, 'regex')
				regex.set('pattern', '.*{0}=.+,{1}=.+$'.format(parent['name'], field))
				regex.set('newunit', familyId)


	if field.upper() not in unitObj.tables.keys():
		tableObj = table()
		tableObj.create(field.upper(), field.upper(), field.upper(), field)
		tableObj.setDummy()
		unitObj.addTable(field.upper(), tableObj)
	else:
		tableObj = unitObj.getTable(field.upper())

	for columnId in struct['items']:
		if 'ZTEMPORARY' in columnId.upper():
			continue

		columnInfo = struct['items'][columnId]
		columnInfo['multiplicity'] = 0

		columnObj = column()
		columnObj.create(columnInfo['id'], columnInfo['name'], columnInfo['udn'], columnInfo['bdcolname'], columnInfo['desc'].strip(), columnInfo['dbn0type'], columnInfo['bdtype'], columnInfo['typeCust'], columnInfo['dataType'], columnInfo['dataUnit'],  columnInfo['multiplicity'])

		if columnObj.dbn0type in ['PK', 'ID']:
			unitObj.addAttribute(columnInfo['id'], columnObj)
		else:
			tableObj.addCounter(columnInfo['id'], columnObj)

	if familyId not in data.keys():
		unitObj = unit()
		unitObj.create(familyId, familyId, name, name, hierarchy)
		unitObj.disableHierarchy()
		data[familyId] = unitObj
	else:
		unitObj = data[familyId]

	if familyId in unitObj.tables.keys():
		tableObj = unitObj.getTable(familyId)
	else:
		tableObj = table()
		tableObj.create(familyId, familyId, familyId, name)
		# tableObj.partitionOf = field.upper()
		unitObj.addTable(familyId, tableObj)


	for columnId in struct['items']:
		if 'ZTEMPORARY' in columnId.upper():
			continue

		columnInfo = struct['items'][columnId]
		columnInfo['multiplicity'] = 0

		columnObj = column()
		columnObj.create(columnInfo['id'], columnInfo['name'], columnInfo['udn'], columnInfo['bdcolname'], columnInfo['desc'].strip(), columnInfo['dbn0type'], columnInfo['bdtype'], columnInfo['typeCust'], columnInfo['dataType'], columnInfo['dataUnit'],  columnInfo['multiplicity'])

		if columnObj.dbn0type in ['PK', 'ID']:
			unitObj.addAttribute(columnInfo['id'], columnObj)
		else:
			tableObj.addCounter(columnInfo['id'], columnObj)

# Returns list of structs
def getStructs(data):
	structList = dict()
	for key in data:
		info = data[key]
		if info['attributes']['isStruct'] == 'True':
			structList[key] = info

	return structList

# Returns list of enums
def getEnums(data):
	enumList = dict()
	for key in data:
		info = data[key]
		try:
			if info['attributes']['isEnum'] == 'True':
				enumList[key] = info
		except KeyError:
			pass

	return enumList
