__doc__ = \
	__version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

from xml.etree.cElementTree import Element
import xml.etree.cElementTree as ET
from lib.functions import xmlReader, writeToFile
from datetime import datetime
from lib.Logger import Logger

# #
# Creates query to truncate all new tables
# #
def generate(data, catalog, config):
	logger = Logger('processLogger').get()
	sqlOutput = ''

	for tableName in data['table']['new']:
		if tableName not in catalog.keys():
			logger.warning('[truncateTable] Table \"{:3s}\" is missing in catalog.'.format(tableName))
			continue
		sqlOutput += 'TRUNCATE TABLE {:3s};\n'.format(tableName)

	if sqlOutput != '':
		writeToFile('truncateTable.sql', sqlOutput)
		logger.debug("  * [truncateTable] Query was created *")
