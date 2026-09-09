__doc__ = \
	__version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

from lib.functions import xmlReader, writeToFile
from lib.Logger import Logger

# #
# Creates query to drop removed tables
# #
def generate(data, catalog, config):
	logger = Logger('processLogger').get()
	sqlOutput = ''

	for tableName in data['table']['new']:
		sqlOutput += 'DROP TABLE IF EXISTS {:s}.{:3s} CASCADE;\n'.format(config['schema'], tableName.lower())

	if sqlOutput != '':
		writeToFile('postgres_dropTable.sql', sqlOutput)
		logger.debug("  * [dropTable] Query was created *")
