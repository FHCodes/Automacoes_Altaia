__doc__ = \
	__version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

import os
import json
from lib.functions import writeToFile
from lib.Logger import Logger

# #
# Merges two JSON loading catalogs into one, being the baseCatalogPath the base for the output
# #
def process(vendor, baseCatalogPath, newCatalogPath, numenclature, config):
	logger = Logger('loadingMerge').get()

	baseCatalog = json.load(open('{0}/loadingCatalog.json'.format(baseCatalogPath)))
	newCatalog = json.load(open('{0}/loadingCatalog.json'.format(newCatalogPath)))

	logger.debug('#################################### Loading Catalog Merging Info ########################################')
	logger.debug('## Vendor: {:34s}                                                     ##'.format(vendor))
	logger.debug('## Output File:  {:80} ##'.format('loadingCatalog.json'))
	logger.debug('################################### Start Loading Catalog Merging ########################################')

	data = dict()

	for table in baseCatalog['measUnits']:
		ossId = table['id']
		if ossId not in data.keys():
			data[ossId] = dict()
			data[ossId]['table'] = table
			data[ossId]['columns'] = getColumns(table['measItems'])
		else:
			logger.warning('  * Duplicated ossId \"{:2s}\" *'.format(ossId))

	for newTable in newCatalog['measUnits']:
		newOssId = newTable.get('id')

		if newOssId in data.keys():
			for attr in config['table'].keys():
				if config['table'][attr] == 'True':
					data[newOssId]['table'][attr] = newTable[attr]

			for newColumn in newTable['measItems']:
				newColumnId = newColumn['id']
				if newColumnId not in data[newOssId]['columns'].keys():
					data[newOssId]['table']['measItems'].append(newColumn)
				else:
					for attr in config['column'].keys():
						if config['column'][attr] == 'True':
							data[newOssId]['columns'][newColumnId][attr] = newColumn[attr]
		else:
			baseCatalog['measUnits'].append(newTable)

	writeToFile('loadingCatalog.json', json.dumps(baseCatalog))
	logger.debug('#################################### End Loading Catalog Merging #########################################')

# #
# Gets columns and comments from a table into dict(column) and list(coments)
# #
def getColumns(columnsList):
	data = dict()
	for column in columnsList:
		columnId = column['id']
		if columnId not in data.keys():
			data[columnId] = column
	return data