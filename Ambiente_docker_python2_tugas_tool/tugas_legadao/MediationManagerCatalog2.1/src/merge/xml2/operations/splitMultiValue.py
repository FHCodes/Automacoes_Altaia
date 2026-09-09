__doc__ = \
	__version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

from lib.Logger import Logger

def process(baseElement, newElement):
	logger = Logger('operationsMerge').get()

	if newElement.get('compressed') != newElement.get('compressed'):
		logger.warning('  * [splitMultiValue][{:5s}] In item \"{:2s}\" differs between base Catalog and new Catalog *'.format('compressed', baseElement.get('id')))

	newSplit = newElement.find('split')
	baseSplit = baseElement.find('split')

	if newSplit.get('delimiter') != baseSplit.get('delimiter'):
		logger.warning('  * [splitMultiValue][{:5s}] In item \"{:2s}\" differs between base Catalog and new Catalog *'.format('delimiter', baseElement.get('id')))

	for newField in newSplit.findall('newField'):
		isNewField = True
		for baseField in baseSplit.findall('newField'):
			if newField.text == baseField.text:
				isNewField = False

		if isNewField:
			baseSplit.append(newField)
