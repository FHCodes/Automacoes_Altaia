__doc__ = \
	__version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

from lib.functions import xmlReader, writeToFile
from lib.Logger import Logger

# #
# Creates query to modify column (RENAME and modify bdtype)
# #
def generate(data, catalog, config):
	logger = Logger('processLogger').get()

	if len(data['column']['change'].keys()) == 0:
		return

	sqlOutputBdcolname = ''
	sqlOutputBDTYPE = ''

	for tableName in data['column']['change'].keys():
		if tableName not in catalog.keys():
			logger.warning('[modifyColumn] Table \"{:3s}\" is missing in catalog.'.format(tableName))
			continue
		for bdcolname in data['column']['change'][tableName].keys():
			if bdcolname not in catalog[tableName].keys():
				logger.warning('[modifyColumn] Column \"{:3s}\" from table \"{:3s}\" is missing in catalog.'.format(bdcolname, tableName))
				continue


			for attribute in data['column']['change'][tableName][bdcolname].keys():
				if attribute.upper() == 'BDTYPE':
					if data['column']['change'][tableName][bdcolname][attribute] == 'NUMBER':
						bdtype = 'NUMERIC'
					elif 'VARCHAR2' in str(data['column']['change'][tableName][bdcolname][attribute]):
						bdtype = data['column']['change'][tableName][bdcolname][attribute].replace('VARCHAR2', 'VARCHAR')
					else:
						bdtype = data['column']['change'][tableName][bdcolname][attribute]
					
					if 'schema' in config and config['schema'] != '' and config['schema'] is not None:
						sqlOutputBDTYPE += 'ALTER TABLE {0}.{1} ALTER COLUMN {2} TYPE {3};\n'.format(config['schema'], tableName, bdcolname,bdtype)
					else:
						sqlOutputBDTYPE += 'ALTER TABLE {0} ALTER COLUMN {1} TYPE {2};\n'.format(tableName, bdcolname, bdtype)
						
				elif attribute.upper() == 'BDCOLNAME':
					if 'schema' in config and config['schema'] != '' and config['schema'] is not None:
						sqlOutputBdcolname += 'ALTER TABLE {0}.{1} RENAME COLUMN {2} TO {3};\n'.format(config['schema'], tableName, data['column']['change'][tableName][bdcolname][attribute], bdcolname)
					else:
						sqlOutputBdcolname += 'ALTER TABLE {0} RENAME COLUMN {1} TO {2};\n'.format(tableName, data['column']['change'][tableName][bdcolname][attribute], bdcolname)

	if sqlOutputBdcolname != '':
		writeToFile('postgres_modifyColumn_bdcolname.sql', sqlOutputBdcolname)
		logger.debug("  * [modifyColumn] Query was created *")

	if sqlOutputBDTYPE != '':
		writeToFile('postgres_modifyColumn_bdype.sql', sqlOutputBDTYPE)
		logger.debug("  * [modifyColumn] Query was created *")