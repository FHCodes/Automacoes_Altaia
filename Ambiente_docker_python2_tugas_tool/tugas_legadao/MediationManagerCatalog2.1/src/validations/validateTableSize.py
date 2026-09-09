__doc__ = \
	__version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

from lib.Logger import Logger

def process(table, config):
	log = Logger('validationsLogger').get()

	size = len(table.findall('column'))

	if size > 985 and size < 999:
		log.warning('TableId "' + table.get('id') + '" is almost at its limit (' + str(size) + ' columns).')
	elif size == 999:
		log.warning('TableId "' + table.get('id') + '" is at its limit (999 columns).')
	elif size >= 1000:
		log.error('TableId "' + table.get('id') + '" its past the column limit (' + str(size) + ' columns).')
