import json

__doc__ = \
    __version__ = '1.1'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>',
               'Version 1.1: Gil Martins <gil-l-martins@alticelabs.com>']

from lib.functions import xmlReader, writeToFile
from collections import OrderedDict
import re
from lib.Logger import Logger
import time


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
            sqlOutput += \
                "  EXECUTE IMMEDIATE 'CREATE INDEX {0}{3}  ON {0}({1}, {2}) TABLESPACE ' || SLD_DBN0_I || ' LOCAL';\n"\
                .format(tableName, config['dateIndex'], mainType, index + 3)
    return sqlOutput


# #
# Creates query to create new tables
# #
def generate(data, catalog, config):
    logger = Logger('processLogger').get()
    
    if not config['liquibase']:
        return
    elif len(data['table']['new']) == 0:
        return

    fileName = "liq_01_newTable.sql"
    changeset_id = "namf:namf-{0}-{1}-{2}".format(config['nomenclature'], fileName[:-4], time.strftime("%Y%m%d%H%M%S"))

    sqlOutput = ""
    sqlOutput += "--liquibase formatted sql\n"
    sqlOutput += "--changeset {0}\n\n".format(changeset_id)

    sqlOutput += "DECLARE\n"
    sqlOutput += "  SLD_DBN0_T VARCHAR2(30) := 'DBN0_T';\n"
    sqlOutput += "  SLD_DBN0_I VARCHAR2(30) := 'DBN0_I';\n"
    sqlOutput += "  PARTITION_NAME_DAY VARCHAR2(30);\n"
    sqlOutput += "  PARTITION_VALUE_DAY VARCHAR2(30);\n"
    sqlOutput += "  PARTITION_NAME_NEXTDAY VARCHAR2(30);\n"
    sqlOutput += "  PARTITION_VALUE_NEXTDAY VARCHAR2(30);\n"
    sqlOutput += "\n"
    sqlOutput += "BEGIN\n"
    sqlOutput += "  PARTITION_NAME_DAY := 'P_' || TO_CHAR(SYSDATE, 'YYYYMMDD');\n"
    sqlOutput += "  PARTITION_VALUE_DAY := TO_CHAR(SYSDATE + 1, 'YYYY-MM-DD') || ' 00:00:00';\n"
    sqlOutput += "  PARTITION_NAME_NEXTDAY := 'P_' || TO_CHAR(SYSDATE + 1, 'YYYYMMDD');\n"
    sqlOutput += "  PARTITION_VALUE_NEXTDAY := TO_CHAR(SYSDATE + 2, 'YYYY-MM-DD') || ' 00:00:00';\n\n"

    sqlOutput += "  EXECUTE IMMEDIATE 'ALTER SESSION SET CURRENT_SCHEMA={0}';\n\n".format(config['schema'])
    
    for tableName in data['table']['new']:
        if tableName not in catalog.keys():
            logger.warning('[liquibase-newTable] Table \"{:3s}\" is missing in catalog.'.format(tableName))
            continue
        createSql = "  EXECUTE IMMEDIATE 'CREATE TABLE {:3s}(SEQ_NUMBER NUMBER(20) NOT NULL, INSERT_DATE TIMESTAMP(3) NOT NULL".format(tableName)

        pkList = ''
        pkSep = ''
        for bdcolname in catalog[tableName].keys():
            createSql += ", {:2s} {:2s}".format(bdcolname, catalog[tableName][bdcolname]['bdtype'])
            if catalog[tableName][bdcolname]['dbn0type'] == 'PK':
                createSql += " NOT NULL"
                pkList += "{:s}{:3s}".format(pkSep, bdcolname)
                pkSep = ", "

        if config['namf']:
            createSql += ", SOURCE_ID VARCHAR2(256), CONTENT_ID VARCHAR2(256)"
        createSql += ") PARTITION BY RANGE({:3s})(PARTITION ' || PARTITION_NAME_DAY || ' VALUES LESS THAN(TIMESTAMP	''' || PARTITION_VALUE_DAY || '''), PARTITION ' || PARTITION_NAME_NEXTDAY || ' VALUES LESS THAN(TIMESTAMP ''' || PARTITION_VALUE_NEXTDAY || ''') ) TABLESPACE ' || SLD_DBN0_T || '';\n".format(config['dateIndex'])
        sqlOutput += validateLineSize(createSql)
        sqlOutput += "  EXECUTE IMMEDIATE 'COMMENT ON TABLE {:3s} is ''{:3s}''';\n".format(tableName, tableName)
        sqlOutput += "  EXECUTE IMMEDIATE 'ALTER TABLE {0} ADD CONSTRAINT {0}PK PRIMARY KEY ({1}) USING INDEX TABLESPACE ' || SLD_DBN0_I || ' NOLOGGING LOCAL';\n".format(tableName, pkList)
        sqlOutput += "  EXECUTE IMMEDIATE 'CREATE INDEX {0}1  ON {0}(SEQ_NUMBER) TABLESPACE ' || SLD_DBN0_I || ' LOCAL';\n".format(tableName)
        sqlOutput += "  EXECUTE IMMEDIATE 'CREATE INDEX {0}2  ON {0}({1}, SEQ_NUMBER) TABLESPACE ' || SLD_DBN0_I || ' LOCAL';\n".format(tableName, config['dateIndex'])
        if config['parameterindex']:
            sqlOutput += addSqlParameterIndex(catalog, config, tableName)
        sqlOutput += "  {0}EXECUTE IMMEDIATE 'ALTER TABLE {1} COMPRESS FOR OLTP';\n".format(('' if config['compressedFlag'].upper() == 'TRUE' else '--'), tableName)
        # if config['schema'] != 's' and config['statslock']:
        #    sqlOutput += "  EXECUTE IMMEDIATE 'begin dbms_stats.lock_table_stats(''{0}'',''{1}''); \nend';\n/".format(config['schema'], tableName)
        sqlOutput += '\n\n'

    sqlOutput += "  COMMIT;\n\n"
    
    sqlOutput += "  BEGIN\n"
    sqlOutput += "    EXECUTE IMMEDIATE 'CREATE SEQUENCE NA_DBN0_SEQ\n"
    sqlOutput += "      START WITH 1\n"
    sqlOutput += "      INCREMENT BY 1\n"
    sqlOutput += "      MAXVALUE 99999999999999999999\n"
    sqlOutput += "      CYCLE\n"
    sqlOutput += "      CACHE 10000';\n\n"
    sqlOutput += "  EXCEPTION\n"
    sqlOutput += "    WHEN OTHERS THEN\n"
    sqlOutput += "      DBMS_OUTPUT.PUT_LINE('Error: ' || SQLERRM);\n"
    sqlOutput += "  END;\n\n"

    sqlOutput += "END;\n/\n"

    writeToFile(fileName, sqlOutput)
    logger.debug("  * [liquibase-newTable] Query was created *")

def validateLineSize(data):
    prefixText = ''
    if len(data) > 2499:
        prefixText = "-- The next table create statement has some extra lines because of sqlplus line limit.\n"
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
