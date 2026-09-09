__doc__ = \
	__version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

from src.inputFormats.generic.excelBase import excelBase
from lib.objects.column import column
from lib.objects.table import table
from lib.objects.unit import unit
from lib.Logger import Logger
import re
from lib.functions import validateInformation
import json

# #
# Cisco EPC excel data processor
# #
def process(docPath, fileConfigName, dataConfig, vendor):
	logger = Logger('processLogger').get()
	catalogType = dataConfig['collector']['collectorType']
	fileConfig = json.load(open('./config/inputConfigs/' + fileConfigName+'.json'))

	info = excelBase(docPath, fileConfig, catalogType).getExcelInfo()

	# Validates the consistency of the data
	validateInformation(info, catalogType, vendor, dataConfig['rules'])

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

		if tableInfo['id'] in unitObj.tables.keys():
			tableObj = unitObj.getTable(tableInfo['id'])
		else:
			unitObj.addTable(tableInfo['id'], tableObj)

		for columnId in info[tableId]['items'].keys():
			columnInfo = info[tableId]['items'][columnId]
			if columnInfo['id'] in tableObj.counters.keys() or columnInfo['id'] in unitObj.attributes.keys():
				logger.warning(' * Duplicated column id \"{:s}\" in table \"{:s}\", new information was discarted * '.format(columnId, tableId))
				continue

			# Validates the dbn0type
			if 'Primary-key' in columnInfo['dbn0type']:
				columnInfo['dbn0type'] = 'PK'
			else:
				if catalogType == 'CM':
					columnInfo['dbn0type'] = 'CM'
				elif 'VARCHAR2(' in columnInfo['bdtype'] or 'TIMESTAMP(' in columnInfo['bdtype']:
					columnInfo['dbn0type'] = 'ID'
				elif catalogType == 'PM':
					columnInfo['dbn0type'] = 'MT'

			columnObj = column()
			columnObj.create(columnInfo['id'], re.sub(r'\<|\>', '', columnInfo['name']), columnInfo['udn'], re.sub(r'-', '', columnInfo['bdcolname']), columnInfo['desc'], columnInfo['dbn0type'], columnInfo['bdtype'], columnInfo['typeCust'], columnInfo['dataType'], columnInfo['dataUnit'], columnInfo['multiplicity'])

			if columnObj.dbn0type in ['PK', 'ID']:
				unitObj.addAttribute(columnInfo['id'], columnObj)
			else:
				tableObj.addCounter(columnInfo['id'], columnObj)

	return data
