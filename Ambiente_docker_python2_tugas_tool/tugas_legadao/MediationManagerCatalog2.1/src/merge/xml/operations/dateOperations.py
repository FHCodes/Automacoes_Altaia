__doc__ = \
	__version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

from lib.Logger import Logger

def process(baseElement, newElement):
	logger = Logger('operationsMerge').get()

	for newOp in newElement.findall('operation'):
		if newOp.get('type') == 'dateOperations':
			isNewConvertTimezone = True
			for baseOp in baseElement.findall('operation'):
				if baseOp.get('type') == 'dateOperations':
					newField = newOp.find('newField')
					baseField = baseOp.find('newField')
					if newField.text == baseField.text:
						isNewConvertTimezone = False

						newField = newOp.find('field')
						baseField = baseOp.find('field')
						if newField.text != baseField.text:
							logger.warning('  * [dateOperations][{:5s}] In unit \"{:3s}\" differs between base Catalog and new Catalog *'.format('field',newElement.get('id')))
						else:
							for newDef in newOp.findall('def'):
								isNewAmount = True
								isNewDateComp = True
								isNewPattern = True
								isNewType = True
								for baseDef in baseOp.findall('def'):
									if newDef.get('amount') == baseDef.get('amount'):
										isNewAmount = False
									if newDef.get('datecomponent') == baseDef.get('datecomponent'):
										isNewDateComp = False
									if newDef.get('pattern') == baseDef.get('pattern'):
										isNewPattern = False
									if newDef.get('type') == baseDef.get('type'):
										isNewType = False

								if isNewPattern:
									baseOp.append(newDef)
								else:
									if isNewAmount:
										logger.warning('  * [dateOperations][{:5s}] In unit \"{:3s}\" differs between base Catalog and new Catalog *'.format('amount',newElement.get('id')))
									if isNewDateComp:
										logger.warning('  * [dateOperations][{:5s}] In unit \"{:3s}\" differs between base Catalog and new Catalog *'.format('datecomponent',newElement.get('id')))
									if isNewType:
										logger.warning('  * [dateOperations][{:5s}] In unit \"{:3s}\" differs between base Catalog and new Catalog *'.format('type',newElement.get('id')))
			if isNewConvertTimezone:
				baseElement.append(newOp)