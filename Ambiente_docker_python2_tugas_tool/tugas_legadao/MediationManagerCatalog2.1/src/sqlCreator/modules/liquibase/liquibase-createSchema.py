__doc__ = \
    __version__ = '1.1'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>',
               'Version 1.1: Gil Martins <gil-l-martins@alticelabs.com>']

from xml.etree.cElementTree import Element
import xml.etree.cElementTree as ET
from lib.functions import xmlReader, writeToFile
from datetime import datetime
from lib.Logger import Logger
import time


# #
# Creates query that creates partition for new table until the year 2030
# #
def generate(data, catalog, config):
    logger = Logger('processLogger').get()
    
    # no schema to create
    if config['schema'] == 's' or '':
        return
    elif not config['liquibase']:
        return
    
    fileName = "liq_00_createSchema_{0}.sql".format(config['schema'])
    changeset_id = "namf:namf-{0}-{1}-{2}".format(config['nomenclature'], fileName[:-4], time.strftime("%Y%m%d%H%M%S"))
    
    sqlOutput = ""
    sqlOutput += "--liquibase formatted sql\n"
    sqlOutput += "--changeset {0}\n".format(changeset_id)
    sqlOutput += "--preconditions onFail:MARK_RAN\n"
    sqlOutput += "--precondition-sql-check expectedResult:0 SELECT count(1) FROM all_users WHERE username = UPPER('{0}');\n\n".format(config['schema'])
    # sqlOutput += "ALTER SESSION SET CURRENT_SCHEMA=SYSTEM;\n\n"
    sqlOutput += "BEGIN\n"
    sqlOutput += "  EXECUTE IMMEDIATE 'CREATE USER {0} IDENTIFIED BY {0}\n".format(config['schema'])
    sqlOutput += "    DEFAULT TABLESPACE DBN0_T\n"
    sqlOutput += "    TEMPORARY TABLESPACE TEMP\n"
    sqlOutput += "    PROFILE DEFAULT\n"
    sqlOutput += "    ACCOUNT UNLOCK';\n"
    sqlOutput += "  EXECUTE IMMEDIATE 'GRANT PRIVS_GESTOR TO {0}';\n".format(config['schema'])
    sqlOutput += "  EXECUTE IMMEDIATE 'GRANT CONNECT TO {0}';\n".format(config['schema'])
    sqlOutput += "  EXECUTE IMMEDIATE 'GRANT ALTER ANY CUBE TO {0}';\n".format(config['schema'])
    sqlOutput += "  EXECUTE IMMEDIATE 'GRANT ALTER SESSION TO {0}';\n".format(config['schema'])
    sqlOutput += "  EXECUTE IMMEDIATE 'GRANT CREATE JOB TO {0}';\n".format(config['schema'])
    sqlOutput += "  EXECUTE IMMEDIATE 'GRANT CREATE PROCEDURE TO {0}';\n".format(config['schema'])
    sqlOutput += "  EXECUTE IMMEDIATE 'GRANT CREATE SEQUENCE TO {0}';\n".format(config['schema'])
    sqlOutput += "  EXECUTE IMMEDIATE 'GRANT CREATE SESSION TO {0}';\n".format(config['schema'])
    sqlOutput += "  EXECUTE IMMEDIATE 'GRANT CREATE SYNONYM TO {0}';\n".format(config['schema'])
    sqlOutput += "  EXECUTE IMMEDIATE 'GRANT CREATE TABLE TO {0}';\n".format(config['schema'])
    sqlOutput += "  EXECUTE IMMEDIATE 'GRANT CREATE TYPE TO {0}';\n".format(config['schema'])
    sqlOutput += "  EXECUTE IMMEDIATE 'GRANT CREATE VIEW TO {0}';\n".format(config['schema'])
    sqlOutput += "  EXECUTE IMMEDIATE 'GRANT CREATE TRIGGER TO {0}';\n".format(config['schema'])
    sqlOutput += "  EXECUTE IMMEDIATE 'ALTER USER {0} DEFAULT ROLE ALL';\n".format(config['schema'])
    sqlOutput += "  EXECUTE IMMEDIATE 'ALTER USER {0} QUOTA UNLIMITED ON DBN0_I';\n".format(config['schema'])
    sqlOutput += "  EXECUTE IMMEDIATE 'ALTER USER {0} QUOTA UNLIMITED ON DBN0_T';\n".format(config['schema'])
    sqlOutput += "END;\n"
    sqlOutput += "/\n"
    
    if sqlOutput != '':
        writeToFile(fileName, sqlOutput)
        logger.debug("  * [{0}] Query was created *".format(fileName[:-4]))