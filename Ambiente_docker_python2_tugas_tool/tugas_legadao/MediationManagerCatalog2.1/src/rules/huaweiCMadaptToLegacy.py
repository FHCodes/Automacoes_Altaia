__doc__ = \
    __version__ = '1.0'
__authors__ = ['Version 0.1: Marco Jeronimo <marco-e-jeronimo@alticelabs.com>']

import json
import os, io
from collections import OrderedDict


# #
#
# #
def process(unitDict, config):
    json_file = config['filename'] + '.json'
    config = json.load(open(os.getcwd() + '/config/customization/' + json_file), object_pairs_hook=OrderedDict)

    for ossId in unitDict.keys():
        if ossId.upper() in config.keys():
            unitObj = unitDict[ossId]
            for attrId in unitObj.attributes.keys():
                if isinstance(config[ossId.upper()], list):
                    #print("IS list {0}: {1}".format(ossId.upper(),config[ossId.upper()]))
                    for listItem in config[ossId.upper()]:
                        #print("attr: {0} lista {1}".format(attrId.upper(),listItem))
                        if isinstance(listItem, dict) and attrId.upper() in listItem["from"].upper():
                            attrObj = unitObj.attributes[attrId]
                            unitObj.update('BDID', (attrId, listItem["to"].upper()))
                            attrObj.update('ID', listItem["to"].upper())
                elif isinstance(config.get(ossId.upper()), dict):
                    if "from" in config[ossId.upper()] and attrId.upper() in config[ossId.upper()]["from"].upper():
                        attrObj = unitObj.attributes[attrId]
                        unitObj.update('BDID', (attrId, config[ossId.upper()]["to"].upper()))
                        attrObj.update('ID', config[ossId.upper()]["to"].upper())

            for tableId in unitObj.tables.keys():
                tableObj = unitObj.getTable(tableId)
                for counterId in tableObj.counters.keys():
                    if isinstance(config[ossId.upper()], list):
                        # print("IS list {0}: {1}".format(ossId.upper(),config[ossId.upper()]))
                        for listItem in config[ossId.upper()]:
                            # print("attr: {0} lista {1}".format(attrId.upper(),listItem))
                            if isinstance(listItem, dict) and counterId.upper() in listItem["from"].upper():
                                counterObj = tableObj.getCounter(counterId)
                                unitObj.update('BDID', (counterId, listItem["to"].upper()))
                                counterObj.update('ID', listItem["to"].upper())
                    elif isinstance(config.get(ossId.upper()), dict):
                        if "from" in config[ossId.upper()] and counterId.upper() in config[ossId.upper()]["from"].upper():
                            counterObj = tableObj.getCounter(counterId)
                            unitObj.update('BDID', (counterId, config[ossId.upper()]["to"].upper()))
                            counterObj.update('ID', config[ossId.upper()]["to"].upper())
