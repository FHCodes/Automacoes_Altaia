__doc__ = \
	__version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

from lib.functions import writeToFile
from lib.Logger import Logger

# #
# Creates query to drop removed columns
# #
def generate(data, catalog, config):
	logger = Logger('processLogger').get()

	if len(data['column']['remove'].keys()) == 0:
		return

	sqlOutput = ''

	for tableName in data['column']['remove'].keys():
		for bdcolname in data['column']['remove'][tableName]:
			sqlOutput += 'ALTER TABLE {:3s} DROP COLUMN {:3s};\n'.format(tableName, bdcolname)

	if sqlOutput != '':
		writeToFile('dropColumn.sql', sqlOutput)
		logger.debug("  * [dropColumn] Query was created *")
