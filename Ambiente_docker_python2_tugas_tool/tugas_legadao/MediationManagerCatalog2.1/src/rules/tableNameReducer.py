__doc__ = \
	__version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

from lib.functions import nameRedutor
import json

def process(unitDict, config):
	configBase = json.load(open('./lib/configuration.json'))
	for unitId in unitDict.keys():
		unitObj = unitDict[unitId]
		for tableId in unitObj.tables.keys():
			tableObj = unitObj.getTable(tableId)
			if len(tableObj.sqlName) > int(configBase['unit']['sqlName']['maxLength']):
				tableObj.sqlName = nameRedutor(tableObj.sqlName, int(configBase['unit']['sqlName']['maxLength']))