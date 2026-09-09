__doc__ = \
	__version__ = '1.0'
__authors__ = [
	'Version 0.1: Gil Martins <gil-l-martins@alticelabs.com>'
]

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
	
	# no schema to create
	if config['schema'] == 's' or '':
		return
	
	sqlOutput = ''
	sqlOutput += "spool createDBN0UsersRoles_AltaiaMediation_{0}_SCHEMA.log\n".format(config['schema'])
	sqlOutput += "PROMPT\n"
	sqlOutput += "PROMPT Executar no schema SYSTEM\n"
	sqlOutput += "PROMPT\n"
	sqlOutput += "PROMPT '[ENTER] PARA INICIAR A INSTALACAO'\n"
	sqlOutput += "PAUSE\n"
	sqlOutput += "PROMPT\n"
	sqlOutput += "SET DEFINE ON;\n"
	sqlOutput += "CREATE USER {0}\n".format(config['schema'])
	sqlOutput += "	IDENTIFIED BY {0}\n".format(config['schema'])
	sqlOutput += "	DEFAULT TABLESPACE DBN0_T\n"
	sqlOutput += "	TEMPORARY TABLESPACE TEMP\n"
	sqlOutput += "	PROFILE DEFAULT\n"
	sqlOutput += "	ACCOUNT UNLOCK;\n"
	sqlOutput += "	-- Roles for {0} \n".format(config['schema'])
	sqlOutput += "	GRANT PRIVS_GESTOR TO {0};\n".format(config['schema'])
	sqlOutput += "	GRANT CONNECT TO {0};\n".format(config['schema'])
	sqlOutput += "	GRANT ALTER ANY CUBE TO {0};\n".format(config['schema'])
	sqlOutput += "	GRANT ALTER SESSION TO {0};\n".format(config['schema'])
	sqlOutput += "	GRANT CREATE JOB TO {0};\n".format(config['schema'])
	sqlOutput += "	GRANT CREATE PROCEDURE TO {0};\n".format(config['schema'])
	sqlOutput += "	GRANT CREATE SEQUENCE TO {0};\n".format(config['schema'])
	sqlOutput += "	GRANT CREATE SESSION TO {0};\n".format(config['schema'])
	sqlOutput += "	GRANT CREATE SYNONYM TO {0};\n".format(config['schema'])
	sqlOutput += "	GRANT CREATE TABLE TO {0};\n".format(config['schema'])
	sqlOutput += "	GRANT CREATE TYPE TO {0};\n".format(config['schema'])
	sqlOutput += "	GRANT CREATE VIEW TO {0};\n".format(config['schema'])
	sqlOutput += "	GRANT CREATE TRIGGER TO {0};\n".format(config['schema'])
	sqlOutput += "	ALTER USER {0} DEFAULT ROLE ALL;\n".format(config['schema'])
	sqlOutput += "	-- 2 Tablespace Quotas for {0}\n".format(config['schema'])
	sqlOutput += "	ALTER USER {0} QUOTA UNLIMITED ON DBN0_I;\n".format(config['schema'])
	sqlOutput += "	ALTER USER {0} QUOTA UNLIMITED ON DBN0_T;\n".format(config['schema'])
	sqlOutput += "SET DEFINE OFF;\n"
	sqlOutput += "spool off\n"
	
	fileName = "createDBN0UsersRoles_AltaiaMediation_{0}_SCHEMA.sql".format(config['schema'])
	
	if sqlOutput != '':
		writeToFile(fileName, sqlOutput)
		logger.debug("  * [{0}] Query was created *".format(fileName[:-4]))