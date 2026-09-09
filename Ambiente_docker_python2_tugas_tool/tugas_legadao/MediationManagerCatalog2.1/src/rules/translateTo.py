__doc__ = \
    __version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

import json
import os, io
from collections import OrderedDict


# #
# Adds a prefix in a field
# #
def process(unitDict, config):
    config = json.load(open(os.getcwd() + '/src/rules/' + config["filename"] + '.json'), object_pairs_hook=OrderedDict)

    for ossId in unitDict.keys():
        unitObj = unitDict[ossId]
        for hierId in unitObj.hierarchyList:
            hierObj = unitObj.hierarchyList[hierId]
            for i, newField in enumerate(hierObj.newFields):
                if newField.upper() in config['preOperations'].keys():
                    hierObj.newFields[i] = str(config['preOperations'][newField.upper()])
                    hierObj.pattern = hierObj.pattern.replace(('<' + newField + '>'),
                                                              ('<' + (hierObj.newFields[i]) + '>'))
                # hierObj.pattern(hierObj.pattern.replace(';'+newField, ';'+ (hierObj.newFields[i])))

        for attrId in unitObj.attributes.keys():
            if attrId.upper() in config['preOperations'].keys():
                attrObj = unitObj.attributes[attrId]
                attrObj.update('UDN', config['preOperations'][attrId.upper()])
                unitObj.update('BDCOLNAME', (attrObj.sqlName, config['preOperations'][attrId.upper()]))
                unitObj.update('BDID', (attrId, config['preOperations'][attrId.upper()]))
                attrObj.update('ID', config['preOperations'][attrId.upper()])
                attrObj.update('BDCOLNAME', config['preOperations'][attrId.upper()])
                for hierId in unitObj.hierarchyList.keys():
                    hierObj = unitObj.hierarchyList[hierId]
                    for idx, hierId in enumerate(hierObj.newFields):
                        if hierId.upper() == config['preOperations'][attrId.upper()]:
                            hierObj.newFields[idx] = config['preOperations'][attrId.upper()]

    for ossId in unitDict.keys():
        unitObj = unitDict[ossId]
        for hierId in unitObj.hierarchyList:
            hierObj = unitObj.hierarchyList[hierId]
            for i, newField in enumerate(hierObj.newFields):
                if newField.upper() in config['operations'].keys():
                    for opObj in config['operations'][newField.upper()]:
                        if (ossId in opObj['units'] and opObj['type'] == 'in') or (
                                ossId not in opObj['units'] and opObj['type'] == 'out'):
                            if newField.upper() in config['operations'].keys():
                                hierObj.newFields[i] = str(opObj['return'])
                                hierObj.pattern = hierObj.pattern.replace(('<' + newField + '>'),
                                                                          ('<' + (hierObj.newFields[i]) + '>'))

        for attrId in unitObj.attributes.keys():
            if attrId.upper() in config['operations'].keys():
                attrObj = unitObj.attributes[attrId]
                for opObj in config['operations'][attrId.upper()]:
                    if (ossId in opObj['units'] and opObj['type'] == 'in') or (
                            ossId not in opObj['units'] and opObj['type'] == 'out'):
                        attrObj.update('UDN', opObj['return'])
                        unitObj.update('BDID', (attrId, opObj['return']))
                        attrObj.update('ID', opObj['return'])
                        unitObj.update('BDCOLNAME', (attrObj.sqlName, opObj['return']))
                        attrObj.update('BDCOLNAME', opObj['return'])
                        for hierId in unitObj.hierarchyList.keys():
                            hierObj = unitObj.hierarchyList[hierId]
                            for idx, hierId in enumerate(hierObj.newFields):
                                if hierId.upper() == config['operations'][attrId.upper()]:
                                    for opObj in config['operations'][attrId.upper()]:
                                        if (unitObj.ossId in opObj['units'] and opObj['type'] == 'in') or (
                                                unitObj.ossId not in opObj['units'] and opObj['type'] == 'out'):
                                            hierObj.newFields[idx] = opObj['return']
