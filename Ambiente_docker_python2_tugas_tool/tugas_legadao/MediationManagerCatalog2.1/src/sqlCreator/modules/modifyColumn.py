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
	
	# despite being a table change, the info comes with the changed columns in the xls
	changed_pk_families = {}
	sqlOutputConstraints = ''

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
					sqlOutputBDTYPE += 'ALTER TABLE {0} MODIFY {1} {2};\n'.format(tableName, bdcolname, data['column']['change'][tableName][bdcolname][attribute])
				elif attribute.upper() == 'BDCOLNAME':
					sqlOutputBdcolname += 'ALTER TABLE {0} RENAME COLUMN {1} TO {2};\n'.format(tableName, data['column']['change'][tableName][bdcolname][attribute], bdcolname)
					
				elif attribute.upper() == 'DBN0TYPE':
					if data['column']['change'][tableName][bdcolname][attribute] == 'PK':
						# here we know there is a change in dbn0type and the column became a PK
						# this means the whole PK must be redefined (once per table)
						if tableName not in changed_pk_families:
							changed_pk_families[tableName] = [col for col in catalog[tableName] if catalog[tableName][col][attribute] == 'PK']  # all pk fields from catalog
							sqlOutputConstraints += 'ALTER TABLE {0} DROP CONSTRAINT {1};\n'.format(tableName.upper(), tableName.upper() + 'PK')
							sqlOutputConstraints += 'ALTER TABLE {0} MODIFY {1} NOT NULL;\n'.format(tableName.upper(), bdcolname.upper())
						else:
							sqlOutputConstraints += 'ALTER TABLE {0} MODIFY {1} NOT NULL;\n'.format(tableName.upper(), bdcolname.upper())
		
		# add the new constraint
		if tableName in changed_pk_families:
			sqlOutputConstraints += 'ALTER TABLE {0} ADD CONSTRAINT {1} PRIMARY KEY ({2}) USING INDEX TABLESPACE DBN0_I NOLOGGING LOCAL;\n\n'.format(tableName.upper(), tableName.upper() + 'PK', ', '.join(changed_pk_families[tableName]))
		
	# # #
	
	if sqlOutputBdcolname != '':
		writeToFile('modifyColumn_bdcolname.sql', sqlOutputBdcolname)
		logger.debug("  * [modifyColumn] Query was created *")

	if sqlOutputBDTYPE != '':
		writeToFile('modifyColumn_bdype.sql', sqlOutputBDTYPE)
		logger.debug("  * [modifyColumn] Query was created *")
		
	if sqlOutputConstraints != '':
		writeToFile('modifyConstraints.sql', sqlOutputConstraints)
		logger.debug("  * [modifyConstraints] Query was created *")
	