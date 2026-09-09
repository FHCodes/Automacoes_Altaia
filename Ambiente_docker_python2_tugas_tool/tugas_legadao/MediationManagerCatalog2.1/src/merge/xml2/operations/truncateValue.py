__doc__ = \
	__version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

from lib.Logger import Logger

def process(baseElement, newElement):
	logger = Logger('operationsMerge').get()

	fieldValues = dict()

	for baseOp in baseElement.findall('operation'):
		if baseOp.get('type') == 'truncateValue':
			for baseDef in baseOp.findall('def'):
				for newField in baseDef.findall('newField'):
					if newField.text in fieldValues.keys():
						logger.warning('  * [truncateValue][{:3s}] In item \"{:2s}\" differs between base Catalog and new Catalog *'.format('newField', baseElement.get('id')))
					else:
						fieldValues[newField.text] = dict()
						fieldValues[newField.text]['start'] = baseDef.get('startIndex')
						fieldValues[newField.text]['end'] = baseDef.get('endIndex')

	for newOp in newElement.findall('operation'):
		if newOp.get('type') == 'truncateValue':
			for baseOp in baseElement.findall('operation'):
				if baseOp.get('type') == 'truncateValue':
					for newDef in newOp.findall('def'):
						missingDef = True
						for baseDef in baseOp.findall('def'):
							sameStart = False
							sameEnd = False
							if baseDef.get('startIndex') == newDef.get('startIndex'):
								sameStart = True
							if baseDef.get('endIndex') == newDef.get('endIndex'):
								sameEnd = True

							for newField in newDef.findall('newField'):
								isNewField = True
								for baseField in baseDef.findall('newField'):
									if baseField.text == newField.text:
										isNewField = False
								if isNewField:
									if newField.text not in fieldValues.keys() and sameStart and sameEnd:
										baseDef.append(newField)
								if newField.text in fieldValues.keys() and (fieldValues[newField.text]['start'] != newDef.get('startIndex') or fieldValues[newField.text]['end'] != newDef.get('endIndex')):
									logger.warning('  * [truncateValue][{:3s}] In item \"{:2s}\" differs between base Catalog and new Catalog for the newField: {:3s}*'.format('startIndex/endIndex', baseElement.get('id'), newField.text))
									missingDef = False

							if sameStart and sameEnd:
								missingDef = False

						if missingDef:
							baseOp.append(newDef)
