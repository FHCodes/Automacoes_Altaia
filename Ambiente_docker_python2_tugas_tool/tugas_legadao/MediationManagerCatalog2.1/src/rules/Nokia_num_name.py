__doc__ = \
	__version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

# #
# From "123(abc)" to "123_abc"
# #
def process(unitDict, config):
	for unitId in unitDict.keys():
		unitObj = unitDict[unitId]
		for tableId in unitObj.tables.keys():
			tableObj = unitObj.getTable(tableId)
			data = unitId.replace(')', '')
			data = data.split('(')
			if len(data) > 1:
				tableObj.sqlName = data[0] + '_' + data[1]
				tableObj.udn = data[0] + '_' + data[1]
