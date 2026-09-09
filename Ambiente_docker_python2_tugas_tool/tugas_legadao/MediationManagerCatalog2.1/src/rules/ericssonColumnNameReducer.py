__doc__ = \
	__version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

from lib.functions import nameRedutor
import json, ast

# #
# Reduces the names of the counters that are to be broken
# #
def process(unitDict, config):
	configBase = ast.literal_eval(json.dumps(json.load(open('./lib/configuration.json'))))
	for ossId in unitDict.keys():
		unitObj = unitDict[ossId]
		for tableId in unitObj.tables.keys():
			tableObj = unitObj.getTable(tableId)

			flag = False
			for counterId in tableObj.counters.keys():
				counterObj = tableObj.getCounter(counterId)
				size = 0
				if counterObj.multiplicity is not '':
					if len(counterObj.sqlName + 'Sub' + str(counterObj.multiplicity)) > int(configBase['item']['sqlName']['maxLength']):
						flag = True
						size = 3 + len(str(counterObj.multiplicity))
					elif len(counterObj.sqlName) > int(configBase['item']['sqlName']['maxLength']):
						flag = True

					if flag:
						counterObj.sqlName = nameRedutor(counterObj.sqlName, int(configBase['item']['sqlName']['maxLength'])-size)
