__doc__ = \
	__version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

from lib.Logger import Logger

def process(baseElement, newElement):
	logger = Logger('operationsMerge').get()

	newOutput = newElement.find('output').text
	baseOutput = baseElement.find('output').text
	if newOutput == baseOutput:
		isNewExecuteCode = False
		newInputDict = dict()
		for inputValue in newElement.findall('input'):
			newInputDict[inputValue.get('id')] = inputValue.text
		newCode = newElement.find('code').text

		baseInputDict = dict()
		for inputValue in baseElement.findall('input'):
			baseInputDict[inputValue.get('id')] = inputValue.text
		baseCode = baseElement.find('code').text

		differs = False
		for newId in newInputDict.keys():
			if newId in baseInputDict.keys():
				if newInputDict[newId] != baseInputDict[newId]:
					differs = True

		if newCode != baseCode:
			logger.warning('  * [executeCode][{:5s}] In unit \"{:3s}\" on the output \"{:2s}\" differs between base Catalog and new Catalog for the same output *'.format('newCode', newElement.get('id'), newOutput))
		if differs:
			logger.warning('  * [executeCode][{:5s}] In unit \"{:3s}\" on the output \"{:2s}\" differs between base Catalog and new Catalog for the same output *'.format('input', newElement.get('id'), newOutput))
