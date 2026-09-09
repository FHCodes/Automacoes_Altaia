__doc__ = \
    __version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

import xml.etree.ElementTree as ET
import os
import re
import json
from lib.functions import writeStringToXML, writeToXML


def process(data, config, parameters):
    config = config['collector']

    root = ET.Element('root', model=config['model'], ossversion=config['version'], vendor=config['vendor'])
    root.append(ET.Comment(config['version']))

    for ossId in sorted(data.keys()):
        unitObj = data[ossId]
        attributesDict = unitObj.attributes
        tableDict = unitObj.tables
        # createPartitionOf = (True if len(tableDict.keys()) > 1 else False)
        for tableId in sorted(tableDict.keys()):
            tableObj = tableDict[tableId]
            if tableObj.isStruct == False or config['vendor'] != 'ERICSSON':
                table = ET.SubElement(root, 'table')
                table.set('id', tableObj.typeId.upper())
                table.set('ossId', ossId.upper())
                table.set('udn', tableObj.udn)
                table.set('tableName', tableObj.sqlName.upper())
                table.set('active', tableObj.active)
                table.set('tech', (config['tech'] if unitObj.tech == '' else unitObj.tech))
                if tableObj.partitionOf != '':
                    table.set('partitionof', tableObj.partitionOf)
                if tableObj.pdfOnly != '':
                    table.set('pdfOnly', tableObj.pdfOnly)

                if config['model'] == 'HUAWEI_OSS_RAN_CM_SRAN':
                    extraDict = unitObj.getExtraCatalog('client')
                # for attr in extraDict.keys():
                #	table.set(attr, extraDict[attr].value)
                else:
                    extraDict = tableObj.getExtraCatalog('client')
                for attr in extraDict.keys():
                    table.set(attr, extraDict[attr].value)

                if tableObj.isDummy:
                    continue

                for attributeId in attributesDict.keys():
                    attributeObj = attributesDict[attributeId]
                    column = ET.SubElement(table, 'column')
                    column.set('id', attributeObj.typeId.upper())
                    column.set('udn', attributeObj.udn)
                    column.set('bdcolname', attributeObj.sqlName.upper())
                    column.set('bdtype', attributeObj.bdtype)
                    column.set('dbn0type', attributeObj.dbn0type)

                    extraDict = attributeObj.getExtraCatalog('client')
                    for attr in extraDict.keys():
                        column.set(attr, extraDict[attr].value)

                for counterId in sorted(tableObj.counters.keys()):
                    counterObj = tableObj.getCounter(counterId)
                    column = ET.SubElement(table, 'column')
                    column.set('id', counterObj.typeId.upper())
                    column.set('udn', counterObj.udn)
                    column.set('bdcolname', counterObj.sqlName.upper())
                    column.set('bdtype', counterObj.bdtype)
                    column.set('dbn0type', counterObj.dbn0type)

                    extraDict = counterObj.getExtraCatalog('client')
                    for attr in extraDict.keys():
                        column.set(attr, extraDict[attr].value)

    # writeToXML(config['nameNomenclature'].replace('#', 'client') + '.xml', ET.ElementTree(root))
    writeStringToXML(config['nameNomenclature'].replace('#', 'client') + '.xml', root)
