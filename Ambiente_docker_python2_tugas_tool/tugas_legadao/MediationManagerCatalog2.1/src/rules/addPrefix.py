__doc__ = \
	__version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

from lib.functions import validateSqlName

# #
# Adds a prefix in a field
# #
def process(unitDict, config):
	for ossId in unitDict.keys():
		unitObj = unitDict[ossId]

		if config['field'] == 'name':
			unitObj.name = config['value'] + unitObj.name

		elif config['field'] == 'desc':
			unitObj.desc = config['value'] + unitObj.desc

		elif config['field'] == 'measuredObject':
			unitObj.measuredObject = config['value'] + unitObj.measuredObject

		else:
			for elementId in unitObj.tables.keys():
				elementObj = unitObj.tables[elementId]
				if config['field'] == 'typeId':
					elementObj.typeId = config['value'] + elementObj.typeId

				elif config['field'] == 'ossId':
					elementObj.ossId = config['value'] + elementObj.ossId


				elif config['field'] == 'sqlName':
					elementObj.sqlName = config['value'] + elementObj.sqlName
					elementObj.sqlName = validateSqlName(elementObj.sqlName)

				elif config['field'] == 'udn':
					elementObj.udn = config['value'] + elementObj.udn

				else:
					print '[Warning] Field "' + config['field'] + '" not found.'
