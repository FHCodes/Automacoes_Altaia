__doc__ = \
	__version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

def process(baseElement, newElement):

	for newField in newElement.findall('field'):
		missingField = True
		for baseField in baseElement.findall('field'):
			if newField.get('id') == baseField.get('id'):
				missingField = False
				for newRegex in newField.findall('regex'):
					missingRegex = True
					for baseRegex in baseField.findall('regex'):
						if newRegex.get('newunit') == baseRegex.get('newunit') and newRegex.get('pattern') == baseRegex.get('pattern'):
							missingRegex = False
					if missingRegex:
						baseField.append(newRegex)
		if missingField:
			baseElement.append(newField)
