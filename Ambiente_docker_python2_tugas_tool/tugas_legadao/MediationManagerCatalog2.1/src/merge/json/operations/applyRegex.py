__doc__ = \
	__version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

def process(baseElement, newElement):

	for newRegex in newElement.findall('regex'):
		pos = 0
		missingPattern = True
		for baseRegex in baseElement.findall('regex'):
			if baseRegex.get('pattern') == newRegex.get('pattern'):
				missingPattern = False
				for newField in newRegex.findall('newField'):
					missingNewField = True
					for baseField in baseRegex.findall('newField'):
						if baseField.text == newField.text:
							missingNewField = False
					if missingNewField:
						baseRegex.append(newField)
		if missingPattern:
			for lRegex in baseElement.findall('regex'):
				if len(newRegex.findall('newField')) >= len(lRegex.findall('newField')):
					baseElement.insert(pos, newRegex)
					missingPattern = False
					break
				pos += 1
			if missingPattern:
				baseElement.insert(pos, newRegex)
