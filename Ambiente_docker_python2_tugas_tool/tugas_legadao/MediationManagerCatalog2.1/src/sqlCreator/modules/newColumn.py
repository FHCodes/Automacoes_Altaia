__doc__ = \
	__version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

from lib.functions import xmlReader, writeToFile
from lib.Logger import Logger

# #
# Creates query to create new columns
# #
def generate(data, catalog, config):
	logger = Logger('processLogger').get()

	if len(data['column']['new'].keys()) == 0:
		return

	sqlOutput = ''

	for tableName in data['column']['new'].keys():
		if tableName not in catalog.keys():
			logger.warning('[newColumn] Table \"{:3s}\" is missing in catalog.'.format(tableName))
			continue
		for bdcolname in data['column']['new'][tableName]:
			if bdcolname not in catalog[tableName].keys():
				logger.warning('[newColumn] Column \"{:3s}\" from table \"{:3s}\" is missing in catalog.'.format(bdcolname, tableName))
				continue
			sqlOutput += 'ALTER TABLE {0} ADD ({1} {2}{3});\n'.format(tableName, bdcolname, catalog[tableName][bdcolname]['bdtype'], (' NOT NULL' if catalog[tableName][bdcolname]['dbn0type'] == 'PK' else ''))

	if sqlOutput != '':
		writeToFile('newColumn.sql', sqlOutput)
		logger.debug("  * [newColumn] Query was created *")
