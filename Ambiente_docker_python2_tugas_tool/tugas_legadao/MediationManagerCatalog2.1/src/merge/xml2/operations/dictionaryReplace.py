__doc__ = \
	__version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

from lib.Logger import Logger

def process(baseElement, newElement):
	logger = Logger('operationsMerge').get()

	for newOp in newElement.findall('operation'):
		if newOp.get('type') == 'dictionaryReplace':
			for baseOp in baseElement.findall('operation'):
				if baseOp.get('type') == 'dictionaryReplace':

					for newItem in newOp.findall('item'):
						isNew = True
						for baseItem in baseOp.findall('item'):
							newKey = newItem.find('key')
							baseKey = baseItem.find('key')
							newValue = newItem.find('value')
							baseValue = baseItem.find('value')
							if newKey.text == baseKey.text:
								if newValue.text != baseValue.text:
									logger.warning('  * [dictionaryReplace][{:5s}] In item \"{:3s}\" differs between base Catalog and new Catalog on key: {:2s}*'.format('value', newElement.get('id'), newKey.text))
								isNew = False
								break
						if isNew:
							baseOp.append(newItem)
