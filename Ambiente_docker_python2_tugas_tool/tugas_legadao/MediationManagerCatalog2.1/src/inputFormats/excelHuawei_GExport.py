__doc__ = \
    __version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

from src.inputFormats.generic.excelBase import excelBase
from lib.objects.column import column
from lib.objects.table import table
from lib.objects.unit import unit
from lib.objects.generic.extraTag import extraTag
from lib.functions import validateInformation
import re
import json
from collections import OrderedDict
from lib.Logger import Logger


# #
# Huawei excel data processor
# #
def process(docPath, fileConfigName, dataConfig, vendor):
    catalogType = dataConfig['collector']['collectorType']
    fileConfig = json.load(open('./config/inputConfigs/' + fileConfigName + '.json'), object_pairs_hook=OrderedDict)

    info = dict()
    techDict = dict()
    for fileName in fileConfig.keys():
        print fileName
        info = excelBase(docPath + fileName, fileConfig[fileName], catalogType).getExcelInfo(info)
        for tableId in info.keys():
            if 'ab' not in info[tableId]['attributes'].keys():
                info[tableId]['attributes']['ab'] = ''
            ab = re.search(r'^(.+?)(&.+?)* .+?$', fileName).group(1).replace('&', ';')
            tech = re.search(r'^.+? (.+?) V.+?$', fileName)
            if tech == None:
                tech = re.search(r'^.+? V.+? (.+?) .+?$', fileName)
            ab = ab + '_' + tech.group(1).replace('&', ';')

            if ab not in info[tableId]['attributes']['ab']:
                if info[tableId]['attributes']['ab'] != '':
                    ab = ';' + ab
                info[tableId]['attributes']['ab'] = info[tableId]['attributes']['ab'] + ab

            if tableId not in techDict.keys():
                techDict[tableId] = ''
            if 'tech' in info[tableId]['attributes'].keys():
                techDict[tableId] = convertTech(info[tableId]['attributes']['tech'], fileName, techDict[tableId])
            else:
                techDict[tableId] = convertTech('', fileName, techDict[tableId])

            for counterId in info[tableId]['items'].keys():
                info[tableId]['items'][counterId]['release'] = re.search(r'^.+? (V.+?) .+?$', fileName).group(1)

    validateInformation(info, catalogType, vendor, dataConfig['rules'])

    data = dict()

    for tableId in info.keys():

        tableInfo = info[tableId]['attributes']
        unitOssId = tableInfo['ossId']

        tableObj = table()
        tableObj.create(tableInfo['id'], tableInfo['ossId'], tableInfo['tableName'], tableInfo['udn'])

        if unitOssId not in data.keys():
            unitObj = unit()
            unitObj.create(tableInfo['ossId'], tableInfo['id'], tableInfo['name'], tableInfo['desc'],
                           tableInfo['hierarchy'])
            unitObj.tech = 'R'
            if '2G' in techDict[tableId]:
                unitObj.tech = unitObj.tech + '2G'
            if '3G' in techDict[tableId]:
                unitObj.tech = unitObj.tech + '3G'
            if '4G' in techDict[tableId]:
                unitObj.tech = unitObj.tech + '4G'
            for attr in tableInfo.keys():
                if attr not in ['id', 'ossId', 'name', 'udn', 'desc', 'tableName', 'hierarchy', 'tech',
                                'disableHierarchy']:
                    unitObj.addExtra(attr, tableInfo[attr])

            data[unitOssId] = unitObj
        else:
            unitObj = data[unitOssId]

        if tableInfo['id'] in unitObj.tables.keys():
            tableObj = unitObj.getTable(tableInfo['id'])
        else:
            unitObj.addTable(tableInfo['id'], tableObj)

        for columnId in info[tableId]['items'].keys():
            columnInfo = info[tableId]['items'][columnId]
            columnInfo['desc'] = re.sub(r'&.+?;', '', columnInfo['desc'])
            if columnInfo['desc'].startswith(' '):
                columnInfo['desc'] = columnInfo['desc'][1:]
            if columnInfo['desc'].endswith(' '):
                columnInfo['desc'] = columnInfo['desc'][:-1]

            columnObj = column()
            columnObj.create(columnInfo['id'], re.sub(r'\<|\>|&', '', columnInfo['name']),
                             re.sub(r'\<|\>|&', '', columnInfo['udn']), re.sub(r'\<|\>', '', columnInfo['bdcolname']),
                             re.sub(r'\<|\>', '', columnInfo['desc']), columnInfo['dbn0type'], columnInfo['bdtype'],
                             columnInfo['typeCust'], columnInfo['dataType'], columnInfo['dataUnit'],
                             columnInfo['multiplicity'])
            for attr in columnInfo.keys():
                if attr not in ['id', 'bdcolname', 'name', 'udn', 'desc', 'bdtype', 'dataType', 'dataUnit',
                                'multiplicity']:
                    columnObj.addExtra(attr, columnInfo[attr], 'oss')

            if columnObj.dbn0type in ['PK', 'ID']:
                unitObj.addAttribute(columnInfo['id'], columnObj)
            else:
                tableObj.addCounter(columnInfo['id'], columnObj)

    return data


def convertTech(cell, fileName, tech):
    if tech == '':
        tech = 'R'

    if ('GSM' in fileName or 'GBTSFunction' in fileName) and '2G' not in tech:
        tech = tech + '2G'
    elif ('UMTS' in fileName or ' NodeBFunction ' in fileName) and '3G' not in tech:
        tech = tech + '3G'
    elif ' eNodeBFunction ' in fileName and '4G' not in tech:
        tech = tech + '4G'
    elif 'RFAFunction' in fileName:
        pass
    elif 'GU V' in fileName and '2G3G' not in tech:
        tech = tech + '2G3G'

    if tech == 'R':
        if 'G' in cell and '2G' not in tech:
            tech = tech + '2G'
        if 'U' in cell and '3G' not in tech:
            tech = tech + '3G'
        if 'L' in cell and '4G' not in tech:
            tech = tech + '4G'
        if 'R' in cell:
            pass

    return tech
