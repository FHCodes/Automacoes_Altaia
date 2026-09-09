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
		#print tableName
		#print '#################'
		#print catalog
		if tableName not in catalog.keys():
			logger.warning('[newColumn] Table \"{:3s}\" is missing in catalog.'.format(tableName))
			continue
		for bdcolname in data['column']['new'][tableName]:
			if bdcolname not in catalog[tableName].keys():
				logger.warning('[newColumn] Column \"{:3s}\" from table \"{:3s}\" is missing in catalog.'.format(bdcolname, tableName))
				continue

			if catalog[tableName][bdcolname]['bdtype'] == 'NUMBER':
				bdtype = 'NUMERIC'
			elif 'VARCHAR2' in str(catalog[tableName][bdcolname]['bdtype']):
				bdtype = catalog[tableName][bdcolname]['bdtype'].replace('VARCHAR2', 'VARCHAR')
			else:
				bdtype = catalog[tableName][bdcolname]['bdtype']

			sqlOutput += 'ALTER TABLE {0}.{1} ADD COLUMN {2} {3}{4};\n'.format(config['schema'], tableName.lower(), bdcolname.lower(), bdtype, (' NOT NULL' if catalog[tableName][bdcolname]['dbn0type'] == 'PK' else ''))

	if sqlOutput != '':
		writeToFile('postgres_newColumn.sql', sqlOutput)
		logger.debug("  * [newColumn] Query was created *")
