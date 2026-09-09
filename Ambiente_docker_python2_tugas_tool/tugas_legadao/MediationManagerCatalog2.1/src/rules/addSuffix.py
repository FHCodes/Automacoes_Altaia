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
			unitObj.name = unitObj.name + config['value']

		elif config['field'] == 'desc':
			unitObj.desc = unitObj.desc + config['value']

		elif config['field'] == 'measuredObject':
			unitObj.measuredObject = unitObj.measuredObject + config['value']

		else:
			for elementId in unitObj.tables.keys():
				elementObj = unitObj.tables[elementId]
				if config['field'] == 'typeId':
					elementObj.typeId = elementObj.typeId + config['value']

				elif config['field'] == 'ossId':
					elementObj.ossId = elementObj.ossId + config['value']


				elif config['field'] == 'sqlName':
					elementObj.sqlName = elementObj.sqlName + config['value']
					elementObj.sqlName = validateSqlName(elementObj.sqlName)

				elif config['field'] == 'udn':
					elementObj.udn = elementObj.udn + config['value']

				else:
					print '[Warning] Field "' + config['field'] + '" not found.'
