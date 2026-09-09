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
            sqlOutput += 'CREATE INDEX {0}{3}  ON {0}({1}, {2}) TABLESPACE &SLD_DBN0_I LOCAL;\n' \
                .format(tableName, config['dateIndex'], mainType, index + 3)
    return sqlOutput


# #
# Creates query to create new tables
# #
def generate(data, catalog, config):
    logger = Logger('processLogger').get()

    if len(data['table']['new']) == 0:
        return

    sqlOutput = 'spool {:3s}.log\n\n'.format(re.sub(r'#', 'client', config['nomenclature']))
    sqlOutput += 'PROMPT ==================== DBN0 Table creation ====================\n\n'
    sqlOutput += 'PROMPT\n\n'
    sqlOutput += 'PROMPT == EXECUTE IN THE CORRECT SCHEMA ==\n\n'
    sqlOutput += 'PROMPT\n\n'
    sqlOutput += 'SET DEFINE ON;\n\n'
    sqlOutput += 'accept SLD_DBN0_T CHAR DEF \'DBN0_T\' PROMPT \'Insert Data tablespace name (default: DBN0_T): \';\n'
    sqlOutput += 'accept SLD_DBN0_I CHAR DEF \'DBN0_I\' PROMPT \'Insert Index tablespace name (default: DBN0_I): \';\n\n'
    sqlOutput += 'COLUMN pnameday NEW_VALUE PARTITION_NAME_DAY\n'
    sqlOutput += 'SELECT \'P_\'||TO_CHAR(SYSDATE,\'YYYYMMDD\') as pnameday from dual;\n'
    sqlOutput += 'COLUMN pvalueday NEW_VALUE PARTITION_VALUE_DAY\n'
    sqlOutput += 'SELECT (\'\'||TO_CHAR(SYSDATE+1,\'YYYY-MM-DD\')||\' 00:00:00\') as pvalueday from dual;\n'
    sqlOutput += 'COLUMN pnamenextday NEW_VALUE PARTITION_NAME_NEXTDAY\n'
    sqlOutput += 'SELECT \'P_\'||TO_CHAR(SYSDATE+1,\'YYYYMMDD\') as pnamenextday from dual;\n'
    sqlOutput += 'COLUMN pvaluenextday NEW_VALUE PARTITION_VALUE_NEXTDAY\n'
    sqlOutput += 'SELECT (\'\'||TO_CHAR(SYSDATE+2,\'YYYY-MM-DD\')||\' 00:00:00\') as pvaluenextday from dual;\n\n'
    sqlOutput += 'PROMPT\n\n'

    for tableName in data['table']['new']:
        if tableName not in catalog.keys():
            logger.warning('[newTable] Table \"{:3s}\" is missing in catalog.'.format(tableName))
            continue
        createSql = 'CREATE TABLE {:3s}(SEQ_NUMBER NUMBER(20) NOT NULL, INSERT_DATE TIMESTAMP(3) NOT NULL'.format(tableName)

        pkList = ''
        pkSep = ''
        for bdcolname in catalog[tableName].keys():
            createSql += ', {:2s} {:2s}'.format(bdcolname, catalog[tableName][bdcolname]['bdtype'])
            if catalog[tableName][bdcolname]['dbn0type'] == 'PK':
                createSql += ' NOT NULL'
                pkList += '{:s}{:3s}'.format(pkSep, bdcolname)
                pkSep = ', '

        if config['namf']:
            createSql += ', SOURCE_ID VARCHAR2(256), CONTENT_ID VARCHAR2(256)'
        createSql += ') PARTITION BY RANGE({:3s})(PARTITION &PARTITION_NAME_DAY VALUES LESS THAN(TIMESTAMP	\'&PARTITION_VALUE_DAY\'), PARTITION &PARTITION_NAME_NEXTDAY VALUES LESS THAN(TIMESTAMP \'&PARTITION_VALUE_NEXTDAY\') ) TABLESPACE &SLD_DBN0_T;\n'.format(config['dateIndex'])
        sqlOutput += validateLineSize(createSql)
        sqlOutput += 'COMMENT ON TABLE {:3s} is \'{:3s}\';\n'.format(tableName, tableName)
        sqlOutput += 'ALTER TABLE {0} ADD CONSTRAINT {0}PK PRIMARY KEY ({1}) USING INDEX TABLESPACE &SLD_DBN0_I NOLOGGING LOCAL;\n'.format(tableName, pkList)
        sqlOutput += 'CREATE INDEX {0}1  ON {0}(SEQ_NUMBER) TABLESPACE &SLD_DBN0_I LOCAL;\n'.format(tableName)
        sqlOutput += 'CREATE INDEX {0}2  ON {0}({1}, SEQ_NUMBER) TABLESPACE &SLD_DBN0_I LOCAL;\n'.format(tableName, config['dateIndex'])
        if config['parameterindex']:
            sqlOutput += addSqlParameterIndex(catalog, config, tableName)
        sqlOutput += '{0}ALTER TABLE {1} COMPRESS FOR OLTP;\n'.format(('' if config['compressedFlag'].upper() == 'TRUE' else '--'), tableName)
        if config['schema'] != 's' and config['statslock']:
            sqlOutput += 'begin dbms_stats.lock_table_stats(\'{0}\',\'{1}\'); \nend;\n/'.format(config['schema'], tableName)
        sqlOutput += '\n\n'

    sqlOutput += 'COMMIT;\n\n'
    sqlOutput += 'CREATE SEQUENCE NA_DBN0_SEQ\n'
    sqlOutput += '  START WITH 1\n'
    sqlOutput += '  INCREMENT BY 1\n'
    sqlOutput += '  MAXVALUE 99999999999999999999\n'
    sqlOutput += '  CYCLE\n'
    sqlOutput += '  CACHE 10000;\n\n'
    sqlOutput += 'SET DEFINE OFF;\n\n'
    sqlOutput += 'SPOOL OFF'

    writeToFile('newTable.sql', sqlOutput)
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
