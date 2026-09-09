__doc__ = \
	__version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

from xml.etree.cElementTree import Element
import xml.etree.cElementTree as ET
from lib.functions import xmlReader, writeToFile
from datetime import datetime
from lib.Logger import Logger

# #
# Creates query that creates partition for new table until the year 2030
# #
def generate(data, catalog, config):
	logger = Logger('processLogger').get()
	sqlOutput = ''

	for tableName in data['table']['new']:
		if tableName not in catalog.keys():
			logger.warning('[partitionGenerator] Table \"{:3s}\" is missing in catalog.'.format(tableName))
			continue
		sqlOutput += 'ALTER TABLE {:s} ADD PARTITION P_{:s} VALUES LESS THAN (TIMESTAMP \'{:s}\');\n'.format(tableName, '20300531', '2030-05-31 00:00:00')

	if sqlOutput != '':
		writeToFile('partitionGenerator.sql', sqlOutput)
		logger.debug("  * [partitionGenerator] Query was created *")
