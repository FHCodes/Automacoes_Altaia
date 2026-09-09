__doc__ = \
	__version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

from lib.Logger import Logger

def process(baseElement, newElement):
	logger = Logger('operationsMerge').get()

	for newOp in newElement.findall('operation'):
		if newOp.get('type') == 'deleteFieldWithPattern':
			for baseOp in baseElement.findall('operation'):
				if baseOp.get('type') == 'deleteFieldWithPattern':
					for newRegex in newOp.findall('regex'):
						notFound = True
						for baseRegex in baseOp.findall('regex'):
							if newRegex.get('pattern') == baseRegex.get('pattern'):
								notFound = False

						if notFound:
							logger.warning('  * [deleteFieldWithPattern][{:5s}] In item \"{:3s}\" differs between base Catalog and new Catalog *'.format('pattern', newElement.get('id')))
