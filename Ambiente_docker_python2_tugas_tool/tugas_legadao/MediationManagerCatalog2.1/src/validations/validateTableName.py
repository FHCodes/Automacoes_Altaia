__doc__ = \
	__version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

import re
from lib.Logger import Logger

def process(table, config):
	log = Logger('validationsLogger').get()

	maxSize = int(config['sqlName']['maxLength'])

	if re.search(r'(\[|\]|\(|\)|-|/|\.| |\<|\>)', table.get('tableName')) is not None:
		log.warning('TableId "' + table.get('id') + '" has tableName with invalid characters.')

	if len(table.get('tableName')) > maxSize:
		log.warning('TableId "' + table.get('id') + '" has tableName too long.')
