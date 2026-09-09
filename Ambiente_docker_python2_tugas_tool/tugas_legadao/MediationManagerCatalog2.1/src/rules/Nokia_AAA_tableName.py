__doc__ = \
	__version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

def process(unitDict, config):
	for unitId in unitDict.keys():
		unitObj = unitDict[unitId]
		for tableId in unitObj.tables.keys():
			tableObj = unitObj.getTable(tableId)
			data = tableId.split('(')[1]
			data = data.replace(')', '')
			tableObj.sqlName = data
