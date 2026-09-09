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

	baseCatalog = json.load(open('{0}/loadingInventory.json'.format(baseCatalogPath)))
	newCatalog = json.load(open('{0}/loadingInventory.json'.format(newCatalogPath)))

	logger.debug('#################################### Loading Inventory Merging Info ########################################')
	logger.debug('## Vendor: {:34s}                                                     ##'.format(vendor))
	logger.debug('## Output File:  {:80} ##'.format('loadingCatalog.json'))
	logger.debug('################################### Start Loading Inventory Merging ########################################')

	data = dict()

	for table in baseCatalog:
		ossId = table['measUnitId']
		if ossId not in data.keys():
			data[ossId] = dict()
			data[ossId] = table
		else:
			logger.warning('  * Duplicated ossId \"{:2s}\" *'.format(ossId))

	for newTable in newCatalog['measUnits']:
		newOssId = newTable.get('measUnitId')

		if newOssId in data.keys():
			for attr in config.keys():
				if config[attr] == 'True':
					data[attr] = newTable[attr]

		else:
			baseCatalog.append(newTable)

	writeToFile('loadingInventory.json', json.dumps(baseCatalog))
	logger.debug('#################################### End Loading Inventory Merging #########################################')
