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
	tranformCatalog = dict()
	tranformCatalog['version'] = "1"
	tranformCatalog['id'] = "{{catalogID}}"
	tranformCatalog['measUnits'] = list()

	for ossId in sorted(data.keys()):
		unitObj = data[ossId]
		unit = OrderedDict()
		unit['id'] = ossId.upper()
		if unitObj.operations != {}:
			operations = unitObj.operations
			if 'item' in operations.keys():
				try:
					if len(unit['measItems']) > 0:
						unit['measItems'] = list()
				except:
					unit['measItems'] = list()
				for itemId in operations['item'].keys():
					item = OrderedDict()
					item['id'] = itemId
					item['operations'] = list()
					for opJson in operations['item'][itemId]:
						item['operations'].append(opJson)

			if 'unit' in operations.keys():
				try:
					if len(unit['operations']) > 0:
						unit['operations'] = list()
				except:
					unit['operations'] = list()
				for typeId in operations['unit'].keys():
					for opJson in operations['unit'][typeId]:
						unit['operations'].append(opJson)

		if 'unit' in rules.keys():
			for rule in rules['unit'].keys():
				for ruleConfig in rules['unit'][rule]['config']:
					unit = rules['unit'][rule]['module'].process(unit, unitObj, ruleConfig)


		tranformCatalog['measUnits'].append(unit)
	writeToFile('transformCatalog.json', json.dumps(tranformCatalog))

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

