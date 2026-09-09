__doc__ = \
	__version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

import json
from lib.functions import validateFieldType

# #
# Converts the typeVendor field as typeCust
# #
def process(unitDict, config):
	configuration = json.load(open('./lib/configuration.json'))

	for ossId in unitDict.keys():
		unitObj = unitDict[ossId]
		for elementId in unitObj.attributes.keys():
			elementObj = unitObj.attributes[elementId]
			elementObj.typeVendor = validateFieldType(elementObj.typeVendor, configuration['item']['typeCust'], 'STRING')

		for tableId in unitObj.tables.keys():
			tableObj = unitObj.tables[tableId]
			for elementId in tableObj.counters.keys():
				elementObj = tableObj.counters[elementId]
				elementObj.typeVendor = validateFieldType(elementObj.typeVendor, configuration['item']['typeCust'], 'STRING')
