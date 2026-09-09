__doc__ = \
	__version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

import re
from lib.Logger import Logger

def process(column, tableId, config):
	log = Logger('validationsLogger').get()

	if re.search(r'([^\x01-\x7F]|"|&|#|\\u|\<|\>)', column.get('desc')) is not None:
		log.warning('ColumnId "' + column.get('id') + '" from tableId "' + tableId + '" has description with invalid characters.')
