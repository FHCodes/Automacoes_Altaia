__doc__ = \
	__version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

from lib.Logger import Logger

def process(baseElement, newElement):
	logger = Logger('operationsMerge').get()

	for newOp in newElement.findall('operation'):
		if newOp.get('type') == 'measurementConverter':
			for baseOp in baseElement.findall('operation'):
				if baseOp.get('type') == 'measurementConverter':
					newConvert = newOp.find('convertTo')
					baseConvert = baseOp.find('convertTo')

					if newConvert.text != baseConvert:
						logger.warning('  * [measurementConverter][{:5s}] In item \"{:2s}\" differs between base Catalog and new Catalog for the same field *'.format('convertTo', baseElement.get('id')))
