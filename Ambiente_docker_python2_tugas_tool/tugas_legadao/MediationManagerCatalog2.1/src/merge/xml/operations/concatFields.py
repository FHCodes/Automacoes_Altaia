__doc__ = \
	__version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

def process(baseElement, newElement):

	for newOp in newElement.findall('operation'):
		if newOp.get('type') == 'concatFields':
			for baseOp in baseElement.findall('operation'):
				if baseOp.get('type') == 'concatFields':

					for newDef in newOp.findall('def'):
						missingDef = True
						isNewDef = False
						for baseDef in baseOp.findall('def'):
							if newDef.get('stringfromfields') == baseDef.get('stringfromfields'):
								for newField in newDef.findall('field'):
									foundField = False
									for baseField in baseDef.findall('field'):
										if newField.text == baseField.text:
											foundField = True
											break
									if not foundField:
										isNewDef = True
										break

								for newField in newDef.findall('newField'):
									foundField = False
									for baseField in baseDef.findall('newField'):
										if newField.text == baseField.text:
											foundField = True
											break
									if not foundField:
										isNewDef = True
										break

						if missingDef or isNewDef:
							baseOp.append(newDef)
