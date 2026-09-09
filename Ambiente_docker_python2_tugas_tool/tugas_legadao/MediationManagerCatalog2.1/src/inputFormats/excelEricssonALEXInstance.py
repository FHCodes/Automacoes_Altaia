__doc__ = \
	__version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

from src.inputFormats.generic.excelBase import excelBase
from lib.objects.column import column
from lib.objects.table import table
from lib.objects.unit import unit
from src.inputFormats.alexInstanceFormat import readAlexFile
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

	# If data is not an excel, them process data as alex (path of the unzip dir of the alex)
	if '.xls' not in docPath:
		docPath = readAlexFile(docPath)

	info = excelBase(docPath, fileConfig, catalogType).getExcelInfo()

	validateInformation(info, catalogType, vendor, dataConfig['rules'])

	data = dict()
	keyWord = ["DBSDOT_PMMIM","DBSDOT_PMMIM","DBSFRT_PMMIM","DBSIOMT_PMMIM","DBSMDPC_PMMIM","DBSNIOMT_PMMIM","DBSPOT_PMMIM","DBSPU_PMMIM","DBSRPCT_PMMIM","LEMSERVICE_PMMIM","OSMDEVICE_PMMIM","OSMMOUNT_PMMIM","OSMPI_PMMIM","OSMPLU_PMMIM","OSMPU_PMMIM","OSMTIPCLINK_PMMIM","LPMDUT_PMMIM","VDBT_PMMIM","VDJT_PMMIM","VDKCT_PMMIM","VDLF_PMMIM","VDPT_PMMIM","VDRPCT_PMMIM","VDTUNNEL_PMMIM","VDVM_PMMIM"]

	for tableId in info.keys():
		tableInfo = info[tableId]['attributes']
		if info[tableId]['items'] == dict():
			continue
		unitOssId = tableInfo['id']
		if tableInfo['function'].upper() in keyWord:
			continue

		tableObj = table()
		tableObj.create(tableInfo['id'], tableInfo['id'], tableInfo['tableName'], tableInfo['udn'])
		tableObj.update('PARTITIONOF', tableInfo['partitionOf'].upper())
		tableObj.update('TECH', dataConfig['collector']['tech'])

		if unitOssId not in data.keys():
			unitObj = unit()
			unitObj.create(unitOssId, unitOssId, tableInfo['name'], tableInfo['desc'].strip(), tableInfo['hierarchy'])
			unitObj.update('TECH', dataConfig['collector']['tech'])
			data[unitOssId] = unitObj
		else:
			unitObj = data[unitOssId]

		#if unitOssId == tableId:
		#	unitObj.update('DESC', tableInfo['DESC'].strip())

		#if tableInfo['hierarchy'] not in unitObj.get('MEASUREDOBJECT') and tableInfo['hierarchy'] != '':
		#	unitObj.update('MEASUREDOBJECT', '{:s}{:s}{:s}'.format(unitObj.get('MEASUREDOBJECT'), ('' if unitObj.get('MEASUREDOBJECT') == '' else ', '), tableInfo['hierarchy']))

		if tableInfo['id'] in unitObj.tables.keys():
			tableObj = unitObj.getTable(tableInfo['id'])
		else:
			unitObj.addTable(tableInfo['id'], tableObj)

		for columnId in info[tableId]['items'].keys():
			if columnId.upper() == 'SUM':
				continue

			columnInfo = info[tableId]['items'][columnId]

			if columnInfo['dataUnit'].upper() not in ['PDF', 'DDM'] and columnInfo['multiplicity'] in ['','1',1]:
				columnInfo['multiplicity'] = 0

			if columnInfo['id'] in tableObj.counters.keys() or columnInfo['id'] in unitObj.attributes.keys():
				logger.warning(' * Duplicated column id \"{:s}\" in table \"{:s}\", new information was discarted * '.format(columnId, tableId))
				continue

			if columnInfo['bdcolname'].startswith('VS'):
				columnInfo['bdcolname'] = columnInfo['bdcolname'][2:]
			columnObj = column()
			columnObj.create(columnInfo['id'], columnInfo['name'], columnInfo['udn'], columnInfo['bdcolname'], columnInfo['desc'].strip(), columnInfo['dbn0type'], columnInfo['bdtype'], columnInfo['typeCust'], columnInfo['dataType'], columnInfo['dataUnit'], columnInfo['multiplicity'])

			if columnObj.dbn0type in ['PK', 'ID']:
				unitObj.addAttribute(columnInfo['id'], columnObj)
			else:
				tableObj.addCounter(columnInfo['id'], columnObj)
	for ossId in data.keys():
		unitObj = data[ossId]
		for tableId in unitObj.tables.keys():
			tableObj = unitObj.getTable(tableId)
			if tableObj.partitionOf == ossId:
				continue
			if tableObj.partitionOf not in data.keys():
				tmpUnitObj = unit()
				tmpUnitObj.create(tableObj.partitionOf, tableObj.partitionOf, tableObj.partitionOf, '', '')
				data[tableObj.partitionOf] = tmpUnitObj

			unitObj.disableHierarchy()
			tmpUnitObj = data[tableObj.partitionOf]
			if unitObj.get('MEASUREDOBJECT') != '':# and re.search('^{0}$|^{0},|,{0}$|,{0},'.format(unitObj.get('MEASUREDOBJECT')), tmpUnitObj.get('MEASUREDOBJECT')) == None:
				tmpUnitObj.update('MEASUREDOBJECT', '{:s}{:s}{:s}'.format(tmpUnitObj.get('MEASUREDOBJECT'), ('' if tmpUnitObj.get('MEASUREDOBJECT') == '' else ','), unitObj.get('MEASUREDOBJECT')))
	return data
