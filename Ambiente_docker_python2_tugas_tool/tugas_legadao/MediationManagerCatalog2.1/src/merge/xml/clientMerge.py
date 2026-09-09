__doc__ = \
    __version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

import xml.etree.ElementTree as ET
from lib.functions import xmlReader, writeStringToXML
from lib.Logger import Logger
import re


# #
# Merges two XML client catalogs into one, being the baseCatalogPath the base for the output
# #
def process(vendor, baseCatalogPath, newCatalogPath, numenclature, config):
    logger = Logger('clientMerge').get()

    baseCatalog = xmlReader(baseCatalogPath.replace('#', 'client'))
    newCatalog = xmlReader(newCatalogPath.replace('#', 'client'))

    logger.debug('#################################### Client Merging Info ########################################')
    logger.debug('## Vendor: {:34s}                                                     ##'.format(vendor))
    logger.debug('## Base: {:40s}   New: {:40s} ##'.format(baseCatalog.get('ossversion'), newCatalog.get('ossversion')))
    logger.debug('## Output File:  {:80} ##'.format(numenclature.replace('#', 'client')))
    logger.debug('################################### Start Client Merging ########################################')

    data = dict()
    comment = list()
    baseCatalog.attrib['ossversion'] = str(baseCatalog.get('ossversion')) + '/' + str(newCatalog.get('ossversion'))

    for table in baseCatalog.findall('table'):
        ossId = table.get('id')
        if ossId is None:
            if ET.tostring(table).upper() not in comment:
                comment.append(ET.tostring(table).upper())
        else:
            ossId = ossId.upper()
            if ossId not in data.keys():
                data[ossId] = dict()
                data[ossId]['table'] = table
                data[ossId]['columns'], data[ossId]['comments'] = getColumns(table)
            else:
                logger.warning('  * Duplicated ossId \"{:2s}\" *'.format(ossId))

    for newTable in newCatalog.findall('table'):
        newOssId = newTable.get('id')
        if newOssId is None:
            if ET.tostring(newTable).upper() not in comment:
                baseCatalog.append(newTable)
        else:
            newOssId = newOssId.upper()
            if newOssId in data.keys():
                tableToAppend = data[newOssId]['table']
                for attr in config['table'].keys():
                    if config['table'][attr] == 'True':
                        if attr == "tech":
                            #if table.get(attr) != newTable.get(attr):
                            #    logger.debug('valor da tech bc: {0} valor da tech nc: {1} - {2}'
                            #                 .format(tableToAppend.get(attr), newTable.get(attr), newTable.get('id')))
                            if '-' in newTable.get(attr):
                                newTechList = newTable.get(attr).split('-')
                                oldTechList = tableToAppend.get(attr).split('-')
                                for nTech in newTechList:
                                    if nTech not in oldTechList:
                                        tableToAppend.set(attr, '{0}-{1}'.format(tableToAppend.get(attr), nTech))
                            else:
                                if re.match(r'R(?:\dG)+\b', tableToAppend.get(attr)) and re.match(r'R(?:\dG)+\b', newTable.get(attr)):
                                    oldTechComponents = set(re.findall(r'\d+G', tableToAppend.get(attr)))
                                    newTechComponents = set(re.findall(r'\d+G', newTable.get(attr)))
                                    combineTech = oldTechComponents.union(newTechComponents)
                                    tableToAppend.set(attr, 'R' + ''.join(sorted(list(combineTech))))
                                else:
                                    if tableToAppend.get(attr) != newTable.get(attr):
                                        tableToAppend.set(attr, '{0}-{1}'.format(tableToAppend.get(attr), newTable.get(attr)))
                                    
                                # logger.debug('Novo valor da tech: {0}'.format(tableToAppend.get(attr)))
                        elif attr == "ab":
                            oldComponents = set()
                            if tableToAppend.get(attr) is not None:
                                oldComponents = set(tableToAppend.get(attr).split(';'))
                            newComponents = set()
                            if newTable.get(attr) is not None:
                                newComponents = set(newTable.get(attr).split(';'))
                            combineAB = oldComponents.union(newComponents)
                            tableToAppend.set(attr, ';'.join(sorted((list(combineAB)))))
                        else:
                            if newTable.get(attr) is not None:
                                tableToAppend.set(attr, newTable.get(attr))

                for newColumn in newTable:
                    newColumnId = newColumn.get('id')
                    if newColumnId is None:
                        if ET.tostring(newColumn).upper() not in data[newOssId]['comments']:
                            tableToAppend.append(newColumn)
                    else:
                        newColumnId = newColumnId.upper()
                        if newColumnId not in data[newOssId]['columns'].keys():
                            tableToAppend.append(newColumn)
                        else:
                            for attr in config['column'].keys():
                                if config['column'][attr] == 'True':
                                    data[newOssId]['columns'][newColumnId].set(attr, newColumn.get(attr))
            else:
                baseCatalog.append(newTable)

    # writeToXML(numenclature.replace('#', 'client'), ET.ElementTree(baseCatalog))
    writeStringToXML(numenclature.replace('#', 'client'), baseCatalog)
    logger.debug('#################################### End Client Merging #########################################')


# #
# Gets columns and comments from a table into dict(column) and list(coments)
# #
def getColumns(table):
    data = dict()
    comment = list()
    for column in table:
        columnId = column.get('id')
        if columnId == None:
            if ET.tostring(column).upper() not in comment:
                comment.append(ET.tostring(column).upper())
        else:
            columnId = columnId.upper()
            if columnId not in data.keys():
                data[columnId] = column
    return data, comment
