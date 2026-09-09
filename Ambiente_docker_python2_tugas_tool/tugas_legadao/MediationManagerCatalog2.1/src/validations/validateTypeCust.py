__doc__ = \
	__version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

from lib.Logger import Logger


def process(item, unitId, config):
	log = Logger('validationsLogger').get()

	if item.get('typeCust') not in ['INTEGER', 'STRING', 'TIMESTAMP', 'FLOAT', 'COUNTER', 'COUNTER32', 'COUNTER64']:
		log.warning('ItemId "' + item.get('id') + '" from unitId "' + unitId + '" has invalid typeCust. (' + item.get('typeCust') + ' not in  ["INTEGER", "STRING", "TIMESTAMP", "FLOAT", "COUNTER", "COUNTER32", "COUNTER64"]')
