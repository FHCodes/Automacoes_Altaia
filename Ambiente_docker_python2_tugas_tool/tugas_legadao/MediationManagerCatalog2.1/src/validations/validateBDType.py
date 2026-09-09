__doc__ = \
	__version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

import re
from lib.Logger import Logger

def process(column, tableId, config):
	log = Logger('validationsLogger').get()

	flag = True

	for bdtype in [r'NUMBER', r'VARCHAR2\([0-9]+\)', r'TIMESTAMP\([0-9]+\)']:
		if re.match(re.compile(bdtype), column.get('bdtype')) is not None:
			return

	if flag:
		log.warning('ColumnId "' + column.get('id') + '" from tableId "' + tableId + '" has invalid bdtype. (' + column.get('bdtype') + ' not in  ["NUMBER", "NUMBER(*)", "VARCHAR(*)", "TIMESTAMP(3)"])')
