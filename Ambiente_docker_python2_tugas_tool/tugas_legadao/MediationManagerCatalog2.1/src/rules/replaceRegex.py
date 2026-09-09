__doc__ = \
	__version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

from lib.functions import validateSqlName
import re

# #
# Adds a prefix in a field
# #
def process(unitDict, config):
	for ossId in unitDict.keys():
		unitObj = unitDict[ossId]

		if config['field'] == 'name':
			try:
				unitObj.name = re.sub(config['regex'], config['value'],  unitObj.name)
			except:
				pass

		elif config['field'] == 'desc':
			try:
				unitObj.desc = re.sub(config['regex'], config['value'],  unitObj.desc)
			except:
				pass

		elif config['field'] == 'measuredObject':
			try:
				unitObj.measuredObject = re.sub(config['regex'], config['value'],  unitObj.measuredObject)
			except:
				pass

		else:
			for elementId in unitObj.tables.keys():
				elementObj = unitObj.tables[elementId]
				if config['field'] == 'typeId':
					try:
						elementObj.typeId = re.sub(config['regex'], config['value'],  elementObj.typeId)
					except:
						pass

				elif config['field'] == 'ossId':
					try:
						elementObj.ossId = re.sub(config['regex'], config['value'], elementObj.ossId)
					except:
						pass

				elif config['field'] == 'sqlName':
					try:
						elementObj.sqlName = re.sub(config['regex'], config['value'], elementObj.sqlName)
						elementObj.sqlName = validateSqlName(elementObj.sqlName)
					except:
						pass

				elif config['field'] == 'udn':
					try:
						elementObj.udn = re.sub(config['regex'], config['value'], elementObj.udn)
					except:
						pass
				else:
					print '[Warning] Field "' + config['field'] + '" not found.'
