__doc__ = \
	__version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

from lib.Logger import Logger

def process(baseElement, newElement):
	logger = Logger('operationsMerge').get()

	for newOp in newElement.findall('operation'):
		if newOp.get('type') == 'fixedValueWithPattern':
			for baseOp in baseElement.findall('operation'):
				if baseOp.get('type') == 'fixedValueWithPattern':

					for newRegex in newOp.findall('regex'):
						isNewRegex = True
						for baseRegex in baseOp.findall('regex'):
							if newRegex.get('pattern') == baseRegex.get('pattern'):
								isNewRegex = False
								for newField in newRegex.findall('newField'):
									isNewField = True
									for baseField in baseRegex.findall('newField'):
										if newField.text == baseField.text:
											isNewField = False
											if newField.get('value') != baseField.get('value'):
												logger.warning('  * [fixedValueWithPattern][{:5s}] In item \"{:2s}\" differs between base Catalog and new Catalog for value: {:3s} *'.format('value', baseElement.get('id'), newField.text))
									if isNewField:
										baseOp.append(newField)
						if isNewRegex:
							baseOp.append(newRegex)
