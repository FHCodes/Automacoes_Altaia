__doc__ = \
	__version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

from lib.functions import xmlReader, writeToFile
from lib.Logger import Logger

# #
# Creates query to modify table (RENAME)
# #
def generate(data, catalog, config):
	logger = Logger('processLogger').get()

	if len(data['table']['change'].keys()) == 0:
		return

	sqlOutput = ''
	for tableName in data['table']['change'].keys():
		for attribute in data['table']['change'][tableName].keys():
			if attribute.upper() == 'TABLENAME':
				sqlOutput += 'ALTER TABLE {0} RENAME TO {1};\n'.format(tableName, data['table']['change'][tableName][attribute])

	if sqlOutput != '':
		writeToFile('postgres_modifyTable.sql', sqlOutput)
		logger.debug("  * [modifyTable] Query was created *")
