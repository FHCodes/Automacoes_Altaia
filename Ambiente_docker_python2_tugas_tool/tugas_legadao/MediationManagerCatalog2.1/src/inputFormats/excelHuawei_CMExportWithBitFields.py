__doc__ = \
    __version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

from src.inputFormats.generic.excelBase import excelBase
from lib.objects.column import column
from lib.objects.table import table
from lib.objects.unit import unit
from lib.functions import validateInformation
from lib.functions import validateUdn
from lib.functions import validateSqlName
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

    bitfieldParamFile = './config/customization/bitfieldParameters.json'

    try:
        bitfieldParam = json.load(open(bitfieldParamFile))
    except:
        bitfieldParam = {}

    data = dict()
    techDict = dict()
    for fileName in fileConfig.keys():
        print fileName
        info = dict()
        info = excelBase(docPath + fileName, fileConfig[fileName], catalogType).getExcelInfo(info)
        validateInformation(info, catalogType, vendor, dataConfig['rules'])

        for tableId in info.keys():
            if 'ab' not in info[tableId]['attributes'].keys():
                info[tableId]['attributes']['ab'] = ''
            ab = re.search(r'^(.+?)(&.+?)* .+?$', fileName).group(1).replace('&', ';')
            tech = re.search(r'^.+? (.+?) V.+?$', fileName)
            if tech == None:
                tech = re.search(r'^.+? V.+? (.+?) .+?$', fileName)
            info[tableId]['attributes']['ab'] = ab + '_' + tech.group(1).replace('&', ';')

            # Dictionary for mapping tech by table
            if tableId not in techDict.keys():
                techDict[tableId] = []
            if 'tech' in info[tableId]['attributes'].keys():
                techDict[tableId] = convertTechV2(info[tableId]['attributes']['tech'], fileName, techDict[tableId])
            else:
                techDict[tableId] = convertTechV2('', fileName, techDict[tableId])

            for counterId in info[tableId]['items'].keys():
                info[tableId]['items'][counterId]['release'] = re.search(r'^.+? (V.+?) .+?$', fileName).group(1)

            tableInfo = info[tableId]['attributes']
            unitOssId = tableInfo['ossId']

            if unitOssId not in data.keys():
                unitObj = unit()
                unitObj.create(unitOssId, tableInfo['id'], tableInfo['name'], tableInfo['desc'], tableInfo['hierarchy'])
                unitObj.addExtra('ab', info[tableId]['attributes']['ab'])
                data[unitOssId] = unitObj
            else:
                unitObj = data[unitOssId]
                if info[tableId]['attributes']['ab'] not in unitObj.extra['ab'].value:
                    unitObj.update('ab', unitObj.extra['ab'].value + ';' + info[tableId]['attributes']['ab'])

            unitObj.tech = 'R'
            if '2G' in techDict[tableId]:
                unitObj.tech = unitObj.tech + '2G'
            if '3G' in techDict[tableId]:
                unitObj.tech = unitObj.tech + '3G'
            if '4G' in techDict[tableId]:
                unitObj.tech = unitObj.tech + '4G'
            if '5G' in techDict[tableId]:
                unitObj.tech = unitObj.tech + '5G'

            for attr in tableInfo.keys():
                if attr not in ['id', 'ossId', 'name', 'udn', 'desc', 'tableName', 'hierarchy', 'tech',
                                'disableHierarchy', 'ab']:
                    unitObj.addExtra(attr, tableInfo[attr])

            if tableId not in unitObj.tables.keys():
                tableObj = table()
                tableObj.create(tableInfo['id'], tableInfo['ossId'], tableInfo['tableName'], tableInfo['udn'])
                unitObj.addTable(tableInfo['id'], tableObj)
            else:
                tableObj = unitObj.getTable(tableId)

            for columnId in info[tableId]['items'].keys():
                if columnId.upper() in tableObj.counters.keys() or columnId.upper() in unitObj.attributes.keys():
                    continue
                else:
                    columnInfo = info[tableId]['items'][columnId]
                    columnInfo['desc'] = re.sub(r'&.+?;', '', columnInfo['desc'])
                    if columnInfo['desc'].startswith(' '):
                        columnInfo['desc'] = columnInfo['desc'][1:]
                    if columnInfo['desc'].endswith(' '):
                        columnInfo['desc'] = columnInfo['desc'][:-1]

                    #
                    # Bit Fields
                    #
                    if columnInfo['dataType'] == 'Bit Field Type':
                        columnInfo['bdtype'] = 'VARCHAR2(2000)'
                        columnInfo['typeCust'] = 'STRING'

                        columnInfo['extraFields'] = re.sub(r'~\d+| ', '', columnInfo['extraFields'])

                        for subCounterName in columnInfo['extraFields'].split(','):
                            bitfieldParam, subCounterNameId = add_table_parameter_sub_parameter(
                                bitfieldParam,
                                tableInfo['id'].upper(),
                                columnInfo['id'].upper(),
                                subCounterName.upper()
                            )

                            columnObj = column()
                            columnObj.create(subCounterNameId,
                                             subCounterName,
                                             validateUdn(columnInfo['udn'] + "." + subCounterName),
                                             validateSqlName(subCounterNameId),
                                             subCounterName,
                                             "CM", "NUMBER", "INTEGER",
                                             "INTEGER", "INTEGER", '')
                            tableObj.addCounter(subCounterNameId, columnObj)

                    columnObj = column()
                    columnObj.create(columnInfo['id'], re.sub(r'\<|\>|&', '', columnInfo['name']),
                                     re.sub(r'\<|\>|\'|@| |\{|\}|&', '', columnInfo['udn']),
                                     re.sub(r'\<|\>', '', columnInfo['bdcolname']),
                                     re.sub(r'\<|\>', '', columnInfo['desc']), columnInfo['dbn0type'],
                                     columnInfo['bdtype'], columnInfo['typeCust'], columnInfo['dataType'],
                                     columnInfo['dataUnit'], columnInfo['multiplicity'])
                    for attr in columnInfo.keys():
                        if attr not in ['id', 'bdcolname', 'name', 'udn', 'desc', 'bdtype', 'dataType', 'dbn0type',
                                        'dataUnit', 'multiplicity', 'unitId', 'extraFields']:
                            columnObj.addExtra(attr, columnInfo[attr], 'oss')

                    if columnObj.dbn0type in ['PK', 'ID']:
                        unitObj.addAttribute(columnInfo['id'].upper(), columnObj)
                    else:
                        tableObj.addCounter(columnInfo['id'].upper(), columnObj)

    with open(bitfieldParamFile, 'w') as jsonfile:
        json.dump(bitfieldParam, jsonfile, indent=4)
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
    elif ' gNodeBFunction ' in fileName and '5G' not in tech:
        tech = tech + '5G'
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
        if 'N' in cell and '5G' not in tech:
            tech = tech + '5G'
        if 'R' in cell:
            pass

    return tech


def convertTechV2(cell, fileName, tech=list()):
    if ('GSM' in fileName or 'GBTSFunction' in fileName) and '2G' not in tech:
        tech.append('2G')
    elif ('UMTS' in fileName or ' NodeBFunction ' in fileName) and '3G' not in tech:
        tech.append('3G')
    elif ' eNodeBFunction ' in fileName and '4G' not in tech:
        tech.append('4G')
    elif ' gNodeBFunction ' in fileName and '5G' not in tech:
        tech.append('5G')
    elif 'gNodeB' in fileName and '5G' not in tech:
        tech.append('5G')
    elif 'RFAFunction' in fileName:
        tech.append('2G')
        tech.append('3G')
        tech.append('4G')
    # pass
    elif 'GU V' in fileName:
        if '2G' not in tech:
            tech.append('2G')
        if '3G' not in tech:
            tech.append('3G')

    if not tech or ' Node ' in fileName:
        if 'G' in cell and '2G' not in tech:
            tech.append('2G')
        if 'U' in cell and '3G' not in tech:
            tech.append('3G')
        if 'L' in cell and '4G' not in tech:
            tech.append('4G')
        if 'N' in cell and '5G' not in tech:
            tech.append('5G')
        if 'R' in cell and '2G' not in tech:
            tech.append('2G')
        if 'R' in cell and '3G' not in tech:
            tech.append('3G')
        if 'R' in cell and '4G' not in tech:
            tech.append('4G')

    return tech


def add_table_parameter_sub_parameter(bitfieldParam, tableId, parameterId, subParameterId):
    logger = Logger('processLogger').get()
    newSubParameterId = subParameterId

    # Check if the table exists
    if tableId not in bitfieldParam:
        bitfieldParam[tableId] = {}

    # Check if the parameter exists
    if parameterId not in bitfieldParam[tableId]:
        bitfieldParam[tableId][parameterId] = []

    if parameterId.upper() != subParameterId.upper():
        # Check if the subparameter exists in this parameter
        if (subParameterId not in bitfieldParam[tableId][parameterId]):
            if (parameterId + "_" + subParameterId) not in bitfieldParam[tableId][parameterId]:
                # validate if other parameter have this subParameter if yes this subParameter are concatenate with parameter.
                for param in bitfieldParam[tableId]:
                    if subParameterId in bitfieldParam[tableId][param]:
                        newSubParameterId = (parameterId + "_" + subParameterId)
                        break

                bitfieldParam[tableId][parameterId].append(newSubParameterId)
                logger.debug("Added sub-parameter '{0}' to '{1}' in '{2}' "
                             "to a bitfieldParameters.json".format(newSubParameterId, parameterId, tableId))
            else:
                newSubParameterId = (parameterId + "_" + subParameterId)
    else:
        newSubParameterId = (parameterId + "_" + subParameterId)
        if (parameterId + "_" + subParameterId) not in bitfieldParam[tableId][parameterId]:
            bitfieldParam[tableId][parameterId].append(newSubParameterId)
            logger.debug("Added sub-parameter '{0}' to '{1}' in '{2}' "
                         "to a bitfieldParameters.json".format(newSubParameterId, parameterId, tableId))

    return bitfieldParam, newSubParameterId
