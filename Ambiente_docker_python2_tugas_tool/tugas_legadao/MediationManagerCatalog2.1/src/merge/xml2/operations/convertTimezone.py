__doc__ = \
	__version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

from lib.Logger import Logger

def process(baseElement, newElement):
	logger = Logger('operationsMerge').get()

	for newOp in newElement.findall('operation'):
		if newOp.get('type') == 'convertTimezone':
			isNewConvertTimezone = True
			for baseOp in baseElement.findall('operation'):
				if baseOp.get('type') == 'convertTimezone':
					newField = newOp.find('newField')
					baseField = baseOp.find('newField')
					if newField.text == baseField.text:
						isNewConvertTimezone = False

						newField = newOp.find('field')
						baseField = baseOp.find('field')
						if newField.text != baseField.text:
							logger.warning('  * [convertTimezone][{:5s}] In unit \"{:3s}\" differs between base Catalog and new Catalog *'.format('field',newElement.get('id')))
						else:
							for newDef in newOp.findall('def'):
								isNewInTz = True
								isNewOutTz = True
								isNewInPt = True
								isNewOutPt = True
								for baseDef in baseOp.findall('def'):
									if newDef.get('in_tz') == baseDef.get('in_tz'):
										isNewInTz = False
									if newDef.get('out_tz') == baseDef.get('out_tz'):
										isNewOutTz = False
									if newDef.get('in_pattern') == baseDef.get('in_pattern'):
										isNewInPt = False
									if newDef.get('out_pattern') == baseDef.get('out_pattern'):
										isNewOutPt = False

								if isNewInPt:
									baseOp.append(newDef)
								else:
									if isNewInTz:
										logger.warning('  * [convertTimezone][{:5s}] differs between base Catalog and new Catalog *'.format('in_tz'))
									if isNewOutTz:
										logger.warning('  * [convertTimezone][{:5s}] differs between base Catalog and new Catalog *'.format('out_tz'))
									if isNewOutPt:
										logger.warning('  * [convertTimezone][{:5s}] differs between base Catalog and new Catalog *'.format('out_pattern'))
			if isNewConvertTimezone:
				baseElement.append(newOp)