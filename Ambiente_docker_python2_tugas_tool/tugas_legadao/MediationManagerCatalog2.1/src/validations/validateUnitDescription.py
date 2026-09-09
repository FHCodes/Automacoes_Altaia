__doc__ = \
	__version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

import re
from lib.Logger import Logger

def process(table, config):
	log = Logger('validationsLogger').get()

	if re.search(r'("|&|#|\\u|\<|\>)', table.get('desc')) is not None:
		log.warning('TableId "' + table.get('id') + '" has description with invalid characters.')

	if table.get('desc') == '':
		log.warning('TableId "' + table.get('id') + '" has description empty.')