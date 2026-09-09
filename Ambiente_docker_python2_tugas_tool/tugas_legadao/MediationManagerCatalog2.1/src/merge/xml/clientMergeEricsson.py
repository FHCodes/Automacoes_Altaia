__doc__ = \
	__version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

import xml.etree.ElementTree as ET
from lib.functions import xmlReader, writeStringToXML
from lib.Logger import Logger
import re
import copy

# #
# Merges two XML client catalogs into one, being the baseCatalogPath the base for the output
# #
def process(vendor, baseCatalogPath, newCatalogPath, numenclature, config):
	logger = Logger('clientMergeEricsson').get()

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

	ossIdMap = dict()


	for table in baseCatalog.findall('table'):
		ossId = table.get('ossId')
		if ossId is None:
			if ET.tostring(table).upper() not in comment:
				comment.append(ET.tostring(table).upper())
		else:
			ossId = ossId.upper()
			if ossId not in data.keys():
				data[ossId] = dict()
				ossIdMap[ossId] = 1
				try:
					tmp = int(re.search(r'_(\d+)$', table.get('tableName')).group(1))
					if tmp > ossIdMap[ossId]:
						ossIdMap[ossId] = tmp
				except:
					pass

			udn = table.get('udn').upper()
			data[ossId][udn] = dict()
			data[ossId][udn]['table'] = table
			data[ossId][udn]['columns'], data[ossId][udn]['comments'] = getColumns(table)

	for newTable in newCatalog.findall('table'):
		newOssId = newTable.get('ossId')
		if newOssId is None:
			if ET.tostring(newTable).upper() not in comment:
				baseCatalog.append(newTable)
		else:
			newOssId = newOssId.upper()
			if newOssId in data.keys():
				newUdn = newTable.get('udn').upper()
				if newUdn in data[newOssId].keys():
					tableToAppend = data[newOssId][newUdn]['table']
					for attr in config['table'].keys():
						if config['table'][attr] == 'True':
							tableToAppend.set(attr, newTable.get(attr))

					for newColumn in newTable:
						newColumnId = newColumn.get('id')
						if newColumnId is None:
							if ET.tostring(newColumn).upper() not in data[newOssId][newUdn]['comments']:
								tableToAppend.append(newColumn)
						else:
							newColumnId = newColumnId.upper()
							if newColumnId not in data[newOssId][newUdn]['columns'].keys():
								if newOssId+'_NEWCOUNTERS' in data[newOssId].keys():
									if newColumnId not in data[newOssId][newOssId+'_NEWCOUNTERS']['columns'].keys():
										#print "New Column: " + newColumn.get('id')
										data[newOssId][newOssId + '_NEWCOUNTERS']['table'].append(newColumn)
								else:
									if len(tableToAppend) >= 980:
										newTableExtended = ET.SubElement(baseCatalog, 'table')
										for attr in tableToAppend.attrib.keys():
											newTableExtended.set(attr, tableToAppend.get(attr))

										newTableExtended.set('udn', newOssId + '_newCounters')
										newTableExtended.set('tableName', newOssId + '_0')
										newTableExtended.set('id', newOssId + '_0')
										for columnCp in tableToAppend.findall('column'):
											if columnCp.get('dbn0type') in ['ID', 'PK']:
												cop = copy.deepcopy(columnCp)
												newTableExtended.append(cop)

										newTableExtended.append(newColumn)
									else:
										tableToAppend.append(newColumn)
							else:
								for attr in config['column'].keys():
									if config['column'][attr] == 'True':
										data[newOssId][newUdn]['columns'][newColumnId].set(attr, newColumn.get(attr))
				else:
					newTable.set('tableName', newTable.get('tableName') + '_' + str(ossIdMap[newOssId]))
					newTable.set('id', newTable.get('ossId') + '_' + str(ossIdMap[newOssId]))
			else:
				#print "New Table: " + newTable.get('id')
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