import json

__doc__ = \
    __version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

from lib.functions import xmlReader, writeToFile
from collections import OrderedDict
import re
from lib.Logger import Logger

def addSqlParameterIndex(catalog, config, tableName):
    sqlOutput = ''
    dataJson = json.load(open('./lib/paramConfig.json'))
    vendor = config['vendor']
    listIndex = []
    mainTypes_position_dict = {}

    for technology, attributes in dataJson[vendor].items():
        for index, element in enumerate(attributes):
            mainTypes_position_dict[element] = index
        mainType = ''
        for bdcolname in catalog[tableName].keys():
            if bdcolname in attributes:
                if mainType == '':
                    mainType = bdcolname
                else:
                    posOld = mainTypes_position_dict[mainType]
                    posNew = mainTypes_position_dict[bdcolname]
                    if posNew < posOld:
                        mainType = bdcolname
        if mainType != '':
            if mainType not in listIndex:
                listIndex.append(mainType)
    if len(listIndex) > 0:
        for index, mainType in enumerate(listIndex):
            sqlOutput += "\n\tCREATE INDEX IF NOT EXISTS IDX_{1}_{4} ON {0}.{1} ({2},{3});".format(
                config['schema'], tableName, config['dateIndex'], mainType, index+2)
            sqlOutput += "\n\tALTER INDEX {0}.IDX_{1}_{2} SET TABLESPACE dbn0_i;"\
                .format(config['schema'], tableName, index+2)
    return sqlOutput

# #
# Creates query to create new tables
# #
def generate(data, catalog, config):
    logger = Logger('processLogger').get()

    if len(data['table']['new']) == 0:
        return

    sqlOutput = "DO $$"
    sqlOutput += "\nDECLARE"
    sqlOutput += "\n\tDBN0T VARCHAR(255);"
    sqlOutput += "\n\tDBN0I VARCHAR(255);"
    sqlOutput += "\n\tPARTITION_INITIAL_DAY VARCHAR(255);"
    sqlOutput += "\n\tPARTITION_NAME_DAY VARCHAR(255);"
    sqlOutput += "\n\tPARTITION_VALUE_DAY VARCHAR(255);"
    sqlOutput += "\n\tPARTITION_NAME_NEXTDAY VARCHAR(255);"
    sqlOutput += "\n\tPARTITION_VALUE_NEXTDAY VARCHAR(255);"

    sqlOutput += "\n\t\nBEGIN"
    sqlOutput += "\n\tRAISE NOTICE '%', '==================== DBN0 Table creation ====================';\n"
    sqlOutput += "\n\t-- Partition names"

    sqlOutput += "\n\tSELECT INTO DBN0T 'dbn0_t';"
    sqlOutput += "\n\tSELECT INTO DBN0I 'dbn0_i';"
    sqlOutput += "\n\tSELECT INTO PARTITION_NAME_DAY 'P_'||TO_CHAR(clock_timestamp(),'YYYYMMDD');"
    sqlOutput += "\n\tSELECT INTO PARTITION_VALUE_DAY TO_CHAR(clock_timestamp() + INTERVAL '1 DAY', 'YYYY-MM-DD 00:00:00');"
    sqlOutput += "\n\tSELECT INTO PARTITION_INITIAL_DAY 0;"

    if config['envirement'].upper() == 'PRD':
        sqlOutput += "\n\tSELECT INTO PARTITION_NAME_NEXTDAY 'P_'||TO_CHAR(clock_timestamp() + INTERVAL '1 DAY','YYYYMMDD');"
        sqlOutput += "\n\tSELECT INTO PARTITION_VALUE_NEXTDAY TO_CHAR(clock_timestamp() + INTERVAL '2 DAY', 'YYYY-MM-DD 00:00:00');"
    elif config['envirement'].upper() == 'DEV':
        sqlOutput += "\n\tSELECT INTO PARTITION_NAME_NEXTDAY 'P_'||TO_CHAR(clock_timestamp() + INTERVAL '15 YEAR','YYYYMMDD');"
        sqlOutput += "\n\tSELECT INTO PARTITION_VALUE_NEXTDAY TO_CHAR(clock_timestamp() + INTERVAL '15 YEAR', 'YYYY-MM-DD 00:00:00');"
    sqlOutput += "\n\t-- Create user if not exists"
    sqlOutput += "\n\tIF NOT EXISTS (SELECT * FROM pg_user WHERE usename = '{0}') THEN".format(config['schema'].lower())
    sqlOutput += "\n\t\tCREATE USER {0} WITH PASSWORD '{0}';".format(config['schema'].lower())
    sqlOutput += "\n\tEND IF;"
    sqlOutput += "\n\t-- Create schema if not exists"
    sqlOutput += "\n\tCREATE SCHEMA IF NOT EXISTS {0} AUTHORIZATION {0};".format(config['schema'])
    sqlOutput += "\n\tEXECUTE format('GRANT CREATE ON TABLESPACE %s TO {0};', DBN0T);".format(config['schema'])
    sqlOutput += "\n\tEXECUTE format('GRANT CREATE ON TABLESPACE %s TO {0};', DBN0I);".format(config['schema'])
    sqlOutput += "\n\t-- Create sequence if not exists"
    sqlOutput += "\n\tCREATE SEQUENCE IF NOT EXISTS {0}.NA_DBN0_SEQ START WITH 1 INCREMENT BY 1 NO MAXVALUE CYCLE CACHE 10000;".format(config['schema'])
    sqlOutput += "\n\tALTER SEQUENCE {0}.NA_DBN0_SEQ OWNER to {0};".format(config['schema'])

    for tableName in data['table']['new']:
        if tableName not in catalog.keys():
            logger.warning('[newTable] Table \"{:3s}\" is missing in catalog.'.format(tableName))
            continue

        sqlOutput += "\n\tCREATE TABLE IF NOT EXISTS {0}.{1} (".format(config['schema'], tableName)
        sqlOutput += "\n\t\tSEQ_NUMBER NUMERIC(20, 0) NOT NULL, \n\t\tINSERT_DATE TIMESTAMP(3) NOT NULL,"
        sqlOutput += "\n\t\tSOURCE_ID VARCHAR(255) NOT NULL, \n\t\tCONTENT_ID VARCHAR(4000) NOT NULL"

        pkList = list()
        pkList.append(config['dateIndex'].upper())

        bdcolname = ''
        for bdcolname in catalog[tableName].keys():
            # Convert NUMBER to NUMERIC
            if catalog[tableName][bdcolname]['bdtype'] == 'NUMBER':
                sqlOutput += ",\n\t\t{0} {1}".format(bdcolname, 'NUMERIC')
            elif 'VARCHAR2' in str(catalog[tableName][bdcolname]['bdtype']):
                sqlOutput += ",\n\t\t{0} {1}".format(bdcolname, catalog[tableName][bdcolname]['bdtype'].replace('VARCHAR2', 'VARCHAR'))
            else:
                sqlOutput += ",\n\t\t{0} {1}".format(bdcolname, catalog[tableName][bdcolname]['bdtype'])

            # If dbn0type is PK, adds NOT NULL constraint
            if catalog[tableName][bdcolname]['dbn0type'] == 'PK':
                if bdcolname not in pkList:
                    pkList.append(bdcolname)
                sqlOutput += " NOT NULL"

        sqlOutput += "\n\t) PARTITION BY RANGE ({0});".format(config['dateIndex'])
        sqlOutput += "\n\n\tALTER TABLE {0}.{1} SET TABLESPACE dbn0_t;".format(config['schema'], tableName)
        #print tableName
        #print catalog[tableName][bdcolname]
        sqlOutput += "\n\tCOMMENT ON TABLE {0}.{1} is '{2}';".format(config['schema'], tableName, catalog[tableName][bdcolname]['name'])

        # Table owner and grants
        sqlOutput += "\n\tALTER TABLE {0}.{1} OWNER to {0};".format(config['schema'], tableName)
        sqlOutput += "\n\tGRANT ALL ON TABLE {0}.{1} TO {0};".format(config['schema'], tableName)
        sqlOutput += "\n\tREVOKE ALL ON {0}.{1} FROM postgres;".format(config['schema'], tableName)
        sqlOutput += "\n\tALTER TABLE {0}.{1} DROP CONSTRAINT IF EXISTS {1}PK;".format(config['schema'], tableName)
        sqlOutput += "\n\tALTER TABLE {0}.{1} ADD CONSTRAINT {1}PK PRIMARY KEY ({2});".format(config['schema'], tableName, ','.join(pkList))
        sqlOutput += "\n\tALTER INDEX {0}.{1}PK SET TABLESPACE dbn0_i;".format(config['schema'], tableName)
        sqlOutput += "\n\tCREATE INDEX IF NOT EXISTS IDX_{1}_0 ON {0}.{1} (SEQ_NUMBER);".format(config['schema'], tableName)
        sqlOutput += "\n\tALTER INDEX {0}.IDX_{1}_0 SET TABLESPACE dbn0_i;".format(config['schema'], tableName)
        sqlOutput += "\n\tCREATE INDEX IF NOT EXISTS IDX_{1}_1 ON {0}.{1} ({2},SEQ_NUMBER);".format(config['schema'], tableName, config['dateIndex'])
        sqlOutput += "\n\tALTER INDEX {0}.IDX_{1}_1 SET TABLESPACE dbn0_i;".format(config['schema'], tableName)

        if config['parameterindex']:
            sqlOutput += addSqlParameterIndex(catalog, config, tableName)

        # Create partitions
        if config['envirement'].upper() == 'PRD':
            sqlOutput += "\n\n\tEXECUTE format('CREATE TABLE IF NOT EXISTS {0}.{1}_%s PARTITION OF {0}.{1} FOR VALUES FROM (to_timestamp(%s)) TO (''%s'');', PARTITION_NAME_DAY, PARTITION_INITIAL_DAY, PARTITION_VALUE_DAY);".format(config['schema'], tableName)
            sqlOutput += "\n\tEXECUTE format('CREATE TABLE IF NOT EXISTS {0}.{1}_%s PARTITION OF {0}.{1} FOR VALUES FROM (''%s'') TO (''%s'');', PARTITION_NAME_NEXTDAY, PARTITION_VALUE_DAY, PARTITION_VALUE_NEXTDAY);".format(config['schema'], tableName)
            # Partition owner and grants
            sqlOutput += "\n\tEXECUTE format('ALTER TABLE {0}.{1}_%s OWNER to {0};', PARTITION_NAME_DAY);".format(config['schema'], tableName)
            sqlOutput += "\n\tEXECUTE format('ALTER TABLE {0}.{1}_%s OWNER to {0};', PARTITION_NAME_NEXTDAY);".format(config['schema'], tableName)
            sqlOutput += "\n\tEXECUTE format('GRANT ALL ON TABLE {0}.{1}_%s TO {0};', PARTITION_NAME_DAY);".format(config['schema'], tableName)
            sqlOutput += "\n\tEXECUTE format('GRANT ALL ON TABLE {0}.{1}_%s TO {0};', PARTITION_NAME_NEXTDAY);".format(config['schema'], tableName)
            sqlOutput += "\n\tEXECUTE format('REVOKE ALL ON {0}.{1}_%s FROM postgres;', PARTITION_NAME_DAY);".format(config['schema'], tableName)
            sqlOutput += "\n\tEXECUTE format('REVOKE ALL ON {0}.{1}_%s FROM postgres;', PARTITION_NAME_NEXTDAY);".format(config['schema'], tableName)
            sqlOutput += "\n\tEXECUTE format('ALTER TABLE {0}.{1}_%s SET TABLESPACE %s;', PARTITION_NAME_DAY, DBN0T);".format(config['schema'], tableName)
            sqlOutput += "\n\tEXECUTE format('ALTER TABLE {0}.{1}_%s SET TABLESPACE %s;', PARTITION_NAME_NEXTDAY, DBN0T);".format(config['schema'], tableName)
        elif config['envirement'].upper() == 'DEV':
            sqlOutput += "\n\n\tEXECUTE format('CREATE TABLE IF NOT EXISTS {0}.{1}_%s PARTITION OF {0}.{1} FOR VALUES FROM (to_timestamp(%s)) TO (''%s'');', PARTITION_NAME_NEXTDAY, PARTITION_INITIAL_DAY, PARTITION_VALUE_NEXTDAY);".format(config['schema'], tableName)
            sqlOutput += "\n\tEXECUTE format('ALTER TABLE {0}.{1}_%s OWNER to {0};', PARTITION_NAME_NEXTDAY);".format(config['schema'], tableName)
            sqlOutput += "\n\tEXECUTE format('GRANT ALL ON TABLE {0}.{1}_%s TO {0};', PARTITION_NAME_NEXTDAY);".format(config['schema'], tableName)
            sqlOutput += "\n\tEXECUTE format('REVOKE ALL ON {0}.{1}_%s FROM postgres;', PARTITION_NAME_NEXTDAY);".format(config['schema'], tableName)
            sqlOutput += "\n\tEXECUTE format('ALTER TABLE {0}.{1}_%s SET TABLESPACE %s;', PARTITION_NAME_NEXTDAY, DBN0T);".format(config['schema'],tableName)

    sqlOutput += "\n\n\tRAISE NOTICE '%', '=============== DBN0 Table creation completed ===============';"
    sqlOutput += "\n\n\tCOMMIT;"
    sqlOutput += "\nEND $$;"

    writeToFile('postgres_newTable' + ('_dev' if config['envirement'].upper() == 'DEV' else '') + '.sql', sqlOutput)
    logger.debug("  * [newTable] Query was created *")

def validateLineSize(data):
    prefixText = ''
    if len(data) > 2499:
        prefixText = '--The next table create statement has some extra lines because of sqlplus line limit.\n'
        listData = data.split(', ')
        data = ''
        line = ''
        for info in listData:
            if len(line) + 2 + len(info) > 2500:
                line += '\n'
                data += line
                line = ''

            line += ('' if line.endswith('(') else ' ') + info + ('' if info.endswith(';\n') or info.endswith(';') else ', ')
            if line.endswith(';') or line.endswith(';\n') :
                data += line
                line = ''

        if line.replace(' ', '') not in [',', '']:
            data += line

    return prefixText + data
