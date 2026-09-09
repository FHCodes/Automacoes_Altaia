__doc__ = \
	__version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

from src.inputFormats.generic.excelBase import excelBase
from lib.objects.column import column
from lib.objects.table import table
from lib.objects.unit import unit
from lib.functions import validateInformation, isDigit
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

	# Configurations to be applied if catalog type is CM (Parameters)
	if catalogType == 'CM':
		#for key in info.keys():
			#print len(info[key]['items'].keys())
			#print info[key]['attributes'].keys()
		info = transformParameters2(info)

	# Validates the consistency of the data
	validateInformation(info, catalogType, vendor, dataConfig['rules'])

	data = dict()
	for objectId in info.keys():
		tableId = info[objectId]['attributes']['id']
		# Validates if family is part of the CM, if not, continue
		#if catalogType == 'CM' and 'cmRestriction' in info[objectId].keys():
		#	if 'CM' not in info[objectId]['cmRestriction']:
		#		continue

		tableInfo = info[objectId]['attributes']
		unitOssId = tableInfo['ossId']

		tableObj = table()
		tableObj.create(tableInfo['id'].upper(), tableInfo['ossId'].upper(), tableInfo['tableName'].upper(), tableInfo['udn'])
		tableObj.tech = dataConfig['collector']['tech']
		if 'partitionOf' in tableInfo.keys():
			tableObj.update('PARTITIONOF', tableInfo['partitionOf'])

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

		if 'isStruct' in tableInfo.keys():
			tableObj.isStruct = True

		for columnId in info[objectId]['items'].keys():
			columnInfo = info[objectId]['items'][columnId]
			columnInfo['id'] = re.sub(r'\<|\>', '', columnInfo['id'].upper())
			#if isDigit(columnInfo['id'].replace('_', '')):
			#	columnInfo['id'] = 'C' + columnInfo['id']
			if columnInfo['id'] in tableObj.counters.keys() or columnInfo['id'] in unitObj.attributes.keys():
				logger.warning(' * Duplicated column id \"{:s}\" in table \"{:s}\", new information was discarted * '.format(columnId, tableId))
				continue

			columnObj = column()
			columnObj.create(columnInfo['id'], re.sub(r'\<|\>', '', columnInfo['name']), re.sub(r'\<|\>', '', columnInfo['udn']), re.sub(r'\<|\>', '', columnInfo['bdcolname'].upper()), re.sub(r'\<|\>', '', columnInfo['desc']), columnInfo['dbn0type'], columnInfo['bdtype'], columnInfo['typeCust'], columnInfo['dataType'], columnInfo['dataUnit'], columnInfo['multiplicity'])

			if columnObj.dbn0type in ['PK', 'ID']:
				unitObj.addAttribute(columnInfo['id'], columnObj)
			else:
				tableObj.addCounter(columnInfo['id'], columnObj)

	return data


# Nokia parametes ruless
def transformParameters(info):
	#print info['TRX']['items']['CHANNEL5SUBSLOT'].keys()
	unitList = info['item'].keys()
	for unitInfo in unitList:
		subFamList = list()
		i = len(info['item'][unitInfo]) - 1
		while i >= 0:
			sItem = info['item'][unitInfo][i]

			if '.' in sItem['id']:
				data = sItem['id'].split('.')
				unitId = unitInfo + '_' + data[0]

				if data[0] not in subFamList:
					subFamList.append(data[0])
					info['unit'][unitId] = dict()
					info['item'][unitId] = list()
					info['unit'][unitId]['id'] = unitId
					info['unit'][unitId]['ossId'] = unitInfo
					info['unit'][unitId]['name'] = unitId
					info['unit'][unitId]['tableName'] = unitId
					info['unit'][unitId]['udn'] = unitId
					info['unit'][unitId]['desc'] = data[0] + ' array from ' + unitInfo
					info['unit'][unitId]['hierarchy'] = info['unit'][unitInfo]['hierarchy'] + '-' + data[0]

				sItem['id'] = data[1]
				sItem['name'] = data[1]
				sItem['udn'] = data[1]
				sItem['bdcolname'] = data[1]
				info['item'][unitId].append(sItem)
				del info['item'][unitInfo][i]
			elif sItem['id'] in subFamList:

				del info['item'][unitInfo][i]
			elif sItem['id'] == '$instance':
				sItem['id'] = 'id'
				sItem['name'] = 'id'
				sItem['udn'] = 'id'
				sItem['bdcolname'] = 'id'
			i -= 1

# Nokia parametes ruless
def transformParameters2(info):
	for unitId in info.keys():
		listToRemove = list()
		for itemId in info[unitId]['items'].keys():
			if '.' in itemId:
				newItemId = info[unitId]['items'][itemId]['id'].split('.')
				newUnitId = '{0}_{1}'.format(unitId, newItemId[0]).upper()
				if newUnitId not in info.keys():
					info[newUnitId] = dict()
					info[newUnitId]['attributes'] = dict()
					info[newUnitId]['attributes']['cmRestriction'] = info[unitId]['attributes']['cmRestriction']
					info[newUnitId]['attributes']['disableHierarchy'] = info[unitId]['attributes']['disableHierarchy']
					info[newUnitId]['attributes']['hierarchy'] = '{0}-{1}'.format(info[unitId]['attributes']['hierarchy'], newItemId[0])
					info[newUnitId]['attributes']['tableName'] = newUnitId
					info[newUnitId]['attributes']['ossId'] = newUnitId
					info[newUnitId]['attributes']['desc'] = '{0} array from {1}'.format(unitId, newUnitId)
					info[newUnitId]['attributes']['id'] = newUnitId
					info[newUnitId]['attributes']['name'] = newUnitId
					info[newUnitId]['attributes']['udn'] = newUnitId
					info[newUnitId]['attributes']['isStruct'] = True
					info[newUnitId]['items'] = dict()
				
				info[newUnitId]['items'][newItemId[1]] = dict()
				info[newUnitId]['items'][newItemId[1]]['name'] = newItemId[1]
				info[newUnitId]['items'][newItemId[1]]['dataType'] = info[unitId]['items'][itemId]['dataType']
				info[newUnitId]['items'][newItemId[1]]['multiplicity'] = info[unitId]['items'][itemId]['multiplicity']
				info[newUnitId]['items'][newItemId[1]]['bdtype'] = info[unitId]['items'][itemId]['bdtype']
				info[newUnitId]['items'][newItemId[1]]['unitId'] = newUnitId
				info[newUnitId]['items'][newItemId[1]]['dataUnit'] = info[unitId]['items'][itemId]['dataUnit']
				info[newUnitId]['items'][newItemId[1]]['desc'] = info[unitId]['items'][itemId]['desc']
				info[newUnitId]['items'][newItemId[1]]['bdcolname'] = newItemId[1]
				info[newUnitId]['items'][newItemId[1]]['id'] = newItemId[1].upper()
				info[newUnitId]['items'][newItemId[1]]['udn'] = newItemId[1]

				listToRemove.append(itemId)
			elif 'pCat' in info[unitId]['items'][itemId].keys():
				if info[unitId]['items'][itemId]['pCat'] != '':
					newItemId = itemId
					newUnitId = '{0}_{1}'.format(unitId, info[unitId]['items'][itemId]['pCat']).upper()


					if newUnitId not in info.keys():
						info[newUnitId] = dict()
						info[newUnitId]['attributes'] = dict()
						info[newUnitId]['attributes']['cmRestriction'] = info[unitId]['attributes']['cmRestriction']
						info[newUnitId]['attributes']['disableHierarchy'] = info[unitId]['attributes']['disableHierarchy']
						info[newUnitId]['attributes']['hierarchy'] = '{0}-{1}'.format(info[unitId]['attributes']['hierarchy'], info[unitId]['items'][itemId]['pCat'])
						info[newUnitId]['attributes']['tableName'] = newUnitId
						info[newUnitId]['attributes']['ossId'] = newUnitId
						info[newUnitId]['attributes']['desc'] = '{0} array from {1}'.format(unitId, newUnitId)
						info[newUnitId]['attributes']['id'] = newUnitId
						info[newUnitId]['attributes']['name'] = newUnitId
						info[newUnitId]['attributes']['udn'] = newUnitId
						info[newUnitId]['attributes']['isStruct'] = True
						info[newUnitId]['items'] = dict()

					info[newUnitId]['items'][newItemId] = dict()
					info[newUnitId]['items'][newItemId]['name'] = newItemId
					info[newUnitId]['items'][newItemId]['name'] = newItemId
					info[newUnitId]['items'][newItemId]['dataType'] = info[unitId]['items'][itemId]['dataType']
					info[newUnitId]['items'][newItemId]['multiplicity'] = info[unitId]['items'][itemId]['multiplicity']
					info[newUnitId]['items'][newItemId]['bdtype'] = info[unitId]['items'][itemId]['bdtype']
					info[newUnitId]['items'][newItemId]['unitId'] = newUnitId
					info[newUnitId]['items'][newItemId]['dataUnit'] = info[unitId]['items'][itemId]['dataUnit']
					info[newUnitId]['items'][newItemId]['desc'] = info[unitId]['items'][itemId]['desc']
					info[newUnitId]['items'][newItemId]['bdcolname'] = newItemId
					info[newUnitId]['items'][newItemId]['id'] = newItemId.upper()
					info[newUnitId]['items'][newItemId]['udn'] = newItemId
					listToRemove.append(itemId)
				elif info[unitId]['items'][itemId]['dataType'].upper() == 'STRUCTURE' or itemId.lower() == '$instance':
					listToRemove.append(itemId)
			elif info[unitId]['items'][itemId]['dataType'].upper() == 'STRUCTURE' or itemId.lower() == '$instance':
				listToRemove.append(itemId)
		for itemId in listToRemove:
			del info[unitId]['items'][itemId]
	return info