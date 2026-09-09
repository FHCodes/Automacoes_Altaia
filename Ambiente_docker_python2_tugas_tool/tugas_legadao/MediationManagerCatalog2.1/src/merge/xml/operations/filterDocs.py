__doc__ = \
	__version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

from lib.Logger import Logger

def process(baseElement, newElement):
	logger = Logger('operationsMerge').get()

	for newOp in newElement.findall('operation'):
		if newOp.get('type') == 'filterDocs':
			for baseOp in baseElement.findall('operation'):
				if baseOp.get('type') == 'filterDocs':

					for newFilter in newOp.findall('filter'):
						isNew = True
						for baseFilter in baseOp.findall('filter'):
							if newFilter.get('field') == baseFilter.get('field'):
								isNew = False
								if newFilter.get('by') != baseFilter.get('by'):
									logger.warning('  * [filterDocs][{:2s}] In unit \"{:3s}\" differs between base Catalog and new Catalog for the same field *'.format('by', newElement.get('id')))
								if newFilter.get('pattern') != baseFilter.get('pattern'):
									baseOp.append(newFilter)
						if isNew:
							baseOp.append(newFilter)
