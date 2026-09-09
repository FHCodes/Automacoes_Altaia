__doc__ = \
	__version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

from lib.Logger import Logger

def process(column, tableId, config):
	log = Logger('validationsLogger').get()

	if column.get('dbn0type') not in ['ID', 'PK', 'ENRICH', 'CM', 'MT']:
		log.warning('ColumnId "' + column.get('id') + '" from tableId "' + tableId + '" has invalid dbn0type.')