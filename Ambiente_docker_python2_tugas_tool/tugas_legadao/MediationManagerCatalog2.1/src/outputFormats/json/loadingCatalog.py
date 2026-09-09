__doc__ = \
	__version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

import xml.etree.ElementTree as ET
from lib.functions import writeToFile
import json
from collections import OrderedDict

def process(data, config, parameters):
	catalog = OrderedDict()
	catalog['id'] = '{{ catalogID }}'
	catalog['version'] = '1'
	catalog['measUnits'] = list()

	for ossId in sorted(data.keys()):
		unitObj = data[ossId]
		tableDict = unitObj.tables
		for tableId in tableDict.keys():
			tableObj = tableDict[tableId]

			tableJson = OrderedDict()
			tableJson['vendorId'] = tableObj.typeId.upper()
			tableJson['useCorrelationFields'] = True
			tableJson['description'] = unitObj.desc
			tableJson['measuredObjects'] = unitObj.measuredObject
			tableJson['granularityField'] = parameters['granularityField']
			tableJson['granularityUnit'] = parameters['granularityUnit']
			tableJson['tableName'] = tableObj.sqlName
			tableJson['name'] = unitObj.name
			tableJson['tech'] = tableObj.tech
			tableJson['partitionOf'] = (tableObj.partitionOf.upper() if tableObj.partitionOf != '' else unitObj.ossId.upper())
			tableJson['active'] = (True if tableObj.active.lower() == 'true' else False)
			tableJson['udn'] = tableObj.udn
			tableJson['id'] = tableObj.typeId.upper()
			tableJson['stateOrigin'] = 'SYSTEM'
			tableJson['objectType'] = 'TBD'
			tableJson['measItems'] = list()
			catalog['measUnits'].append(tableJson)

			if tableObj.isDummy:
				continue

			attributeDict = unitObj.attributes
			for attributeId in attributeDict.keys():
				attributeObj = attributeDict[attributeId]
				itemJson = OrderedDict()
				itemJson['vendorId'] = attributeObj.typeId.upper()
				itemJson['description'] = attributeObj.desc
				itemJson['columnName'] = attributeObj.sqlName.upper()
				itemJson['type'] = attributeObj.bdtype
				itemJson['unitVendor'] = (attributeObj.unitVendor if attributeObj.unitVendor != '' else attributeObj.typeVendor)
				itemJson['typeVendor'] = attributeObj.typeVendor
				itemJson['typeCust'] = attributeObj.typeCust
				itemJson['measItemType'] = attributeObj.dbn0type
				itemJson['active'] = True
				itemJson['udn'] = attributeObj.udn
				itemJson['id'] = attributeObj.typeId.upper()
				itemJson['stateOrigin'] = 'SYSTEM'
				itemJson['name'] = attributeObj.name
				tableJson['measItems'].append(itemJson)

			countersDict = tableObj.counters
			for counterId in countersDict.keys():
				counterObj = countersDict[counterId]
				itemJson = OrderedDict()
				itemJson['vendorId'] = counterObj.typeId.upper()
				itemJson['description'] = counterObj.desc
				itemJson['columnName'] = counterObj.sqlName.upper()
				itemJson['type'] = counterObj.bdtype
				itemJson['unitVendor'] = (counterObj.unitVendor if counterObj.unitVendor != '' else counterObj.typeVendor)
				itemJson['typeVendor'] = counterObj.typeVendor
				itemJson['typeCust'] = counterObj.typeCust
				itemJson['measItemType'] = counterObj.dbn0type
				itemJson['active'] = True
				itemJson['udn'] = counterObj.udn
				itemJson['id'] = counterObj.typeId.upper()
				itemJson['stateOrigin'] = 'SYSTEM'
				itemJson['name'] = (counterObj.name if counterObj.name != '' else counterObj.typeId)
				tableJson['measItems'].append(itemJson)

	writeToFile('loadingCatalog.json', json.dumps(catalog))
