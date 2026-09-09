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

            for counterId in tableObj.counters.keys():
                counterObj = tableObj.getCounter(counterId)
                if len(counterObj.sqlName) > int(configBase['item']['sqlName']['maxLength']):
                    dt = {'MESSAGES': 'MSG', 'COUNTERS': 'CNT', 'DEFAULT': 'DEF', 'CHARGING': 'CRG', 'INSTALL': 'IST',
                          'DIAMETER': 'DMT', 'MOBILE': 'MBL'}
                    for key in dt.keys():
                        if key in counterObj.sqlName.upper():
                            counterObj.sqlName = counterObj.sqlName.upper().replace(key, dt[key])
                    counterObj.sqlName = nameRedutor(counterObj.sqlName.replace('.', ''),
                                                     int(configBase['item']['sqlName']['maxLength']))
                    if len(counterObj.sqlName) > int(configBase['item']['sqlName']['maxLength']):
                        counterObj.sqlName = counterObj.sqlName.replace('_', '')
