__doc__ = \
	__version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

from lib.functions import writeToFile
import pkgutil
from collections import OrderedDict
import src.outputFormats.json.operations
import json

def process(data, config, parameters):
	rules = getOperations(config['outputFormat']['operationsCatalog'])
	config = config['collector']
	inventoryCatalog = list()
	for ossId in data.keys():
		unitObj = data[ossId]
		for tableId in unitObj.tables.keys():
			tableObj = unitObj.tables[tableId]
			tableDict = OrderedDict()
			tableDict['measUnitId'] = tableObj.typeId.upper()
			tableDict['schemaName'] = '{{schemaName}}'
			tableDict['datasourceId'] = '{{datasourceID}}'
			tableDict['tableName'] = tableObj.sqlName
			tableDict['catalogId'] = '{{catalogID}}'
			inventoryCatalog.append(tableDict)

	writeToFile('loadingInventory.json', json.dumps(inventoryCatalog))

def getOperations(config):
	outFormatList = OrderedDict()
	for key in config:
		outFormatList[key] = OrderedDict()
		for importer, packageName, xx in pkgutil.iter_modules(src.outputFormats.json.operations.__path__):
			if packageName in config[key].keys():
				outFormatList[key][packageName] = dict()
				outFormatList[key][packageName]['module'] = importer.find_module(packageName).load_module(packageName)
				outFormatList[key][packageName]['config'] = config[key][packageName]
	return outFormatList

