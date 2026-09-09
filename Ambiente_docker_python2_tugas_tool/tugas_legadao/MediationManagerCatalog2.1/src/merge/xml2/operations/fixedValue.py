__doc__ = \
	__version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

from lib.Logger import Logger

def process(baseElement, newElement):
	logger = Logger('operationsMerge').get()

	for newOp in newElement.findall('operation'):
		if newOp.get('type') == 'fixedValue':
			for baseOp in baseElement.findall('operation'):
				if baseOp.get('type') == 'fixedValue':

					for newField in newOp.findall('newField'):
						isNew = True
						for baseField in baseOp.findall('newField'):
							if newField.text == baseField.text:
								isNew = False
								if newField.get('value') != baseField.get('value'):
									logger.warning('  * [fixedValue][{:5s}] In unit \"{:2s}\" differs between base Catalog and new Catalog for value: {:3s} *'.format('value', baseElement.get('id'), newField.text))
						if isNew:
							baseOp.append(newField)
