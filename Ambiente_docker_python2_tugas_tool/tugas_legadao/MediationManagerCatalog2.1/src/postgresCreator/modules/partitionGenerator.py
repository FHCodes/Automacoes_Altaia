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

	if len(data['table']['new']) == 0:
		return

	sqlOutput = "DO $$"
	sqlOutput += "\nDECLARE"
	sqlOutput += "\n\tDBN0T VARCHAR(255);"
	sqlOutput += "\n\tPARTITION_INITIAL_DAY VARCHAR(255);"
	sqlOutput += "\n\tPARTITION_NAME_DAY VARCHAR(255);"
	sqlOutput += "\n\tPARTITION_VALUE_DAY VARCHAR(255);"
	sqlOutput += "\n\tPARTITION_NAME_NEXTDAY VARCHAR(255);"
	sqlOutput += "\n\tPARTITION_VALUE_NEXTDAY VARCHAR(255);"

	sqlOutput += "\n\t\nBEGIN"
	sqlOutput += "\n\tRAISE NOTICE '%', '==================== DBN0 Table creation ====================';\n"
	sqlOutput += "\n\t-- Partition names"

	sqlOutput += "\n\tSELECT INTO DBN0T 'dbn0_t';"
	sqlOutput += "\n\tSELECT INTO PARTITION_NAME_DAY 'P_'||TO_CHAR(clock_timestamp(),'YYYYMMDD');"
	sqlOutput += "\n\tSELECT INTO PARTITION_VALUE_DAY TO_CHAR(clock_timestamp() + INTERVAL '1 DAY', 'YYYY-MM-DD 00:00:00');"
	sqlOutput += "\n\tSELECT INTO PARTITION_INITIAL_DAY 0;"
	sqlOutput += "\n\tSELECT INTO PARTITION_NAME_NEXTDAY 'P_'||TO_CHAR(clock_timestamp() + INTERVAL '15 YEAR','YYYYMMDD');"
	sqlOutput += "\n\tSELECT INTO PARTITION_VALUE_NEXTDAY TO_CHAR(clock_timestamp() + INTERVAL '15 YEAR', 'YYYY-MM-DD 00:00:00');"

	for tableName in data['table']['new']:

		if tableName not in catalog.keys():
			logger.warning('[partitionGenerator] Table \"{:3s}\" is missing in catalog.'.format(tableName))
			continue
		sqlOutput += "\n\n\tEXECUTE format('CREATE TABLE IF NOT EXISTS {0}.{1}_%s PARTITION OF {0}.{1} FOR VALUES FROM (to_timestamp(%s)) TO (''%s'');', PARTITION_NAME_NEXTDAY, PARTITION_INITIAL_DAY, PARTITION_VALUE_NEXTDAY);".format(
			config['schema'], tableName)
		sqlOutput += "\n\tEXECUTE format('ALTER TABLE {0}.{1}_%s OWNER to {0};', PARTITION_NAME_NEXTDAY);".format(
			config['schema'], tableName)
		sqlOutput += "\n\tEXECUTE format('GRANT ALL ON TABLE {0}.{1}_%s TO {0};', PARTITION_NAME_NEXTDAY);".format(
			config['schema'], tableName)
		sqlOutput += "\n\tEXECUTE format('REVOKE ALL ON {0}.{1}_%s FROM postgres;', PARTITION_NAME_NEXTDAY);".format(
			config['schema'], tableName)
		sqlOutput += "\n\tEXECUTE format('ALTER TABLE {0}.{1}_%s SET TABLESPACE %s;', PARTITION_NAME_NEXTDAY, DBN0T);".format(
			config['schema'], tableName)

	sqlOutput += "\n\n\tRAISE NOTICE '%', '=============== DBN0 Table creation completed ===============';"
	sqlOutput += "\n\n\tCOMMIT;"
	sqlOutput += "\nEND $$;"

	if sqlOutput != '':
		writeToFile('partitionGenerator.sql', sqlOutput)
		logger.debug("  * [partitionGenerator] Query was created *")
