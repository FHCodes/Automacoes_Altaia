__doc__ = \
	__version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

from lib.Logger import Logger

def process(baseElement, newElement):
	logger = Logger('operationsMerge').get()

	for newOp in newElement.findall('operation'):
		if newOp.get('type') == 'enrichment':
			for baseOp in baseElement.findall('operation'):
				if baseOp.get('type') == 'enrichment':

					for newScope in newOp.findall('scope'):
						isNew = True
						for baseScope in baseOp.findall('scope'):
							if newScope.text == baseScope.text:
								isNew = False
						if isNew:
							logger.warning('  * [enrichment][{:5s}] In unit \"{:2s}\" new Catalog has a new value: {:1s} *'.format('scope', newElement.get('id'), newScope.text))

					for newCorrKey in newOp.findall('corrKey'):
						isNew = True
						for baseCorrKey in baseOp.findall('corrKey'):
							if newCorrKey.text == baseCorrKey.text:
								isNew = False
						if isNew:
							logger.warning('  * [enrichment][{:5s}] In unit \"{:2s}\" new Catalog has a new value: {:1s} *'.format('corrKey', newElement.get('id'), newCorrKey.text))

					for newField in newOp.findall('newField'):
						isNew = True
						for baseField in baseOp.findall('newField'):
							if newField.text == baseField.text:
								isNew = False
						if isNew:
							logger.warning('  * [enrichment][{:5s}] In unit \"{:2s}\" new Catalog has a new value: {:1s} *'.format('newField', newElement.get('id'), newField.text))
