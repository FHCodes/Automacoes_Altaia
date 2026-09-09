__doc__ = \
	__version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

def process(baseElement, newElement):

	for newOp in newElement.findall('operation'):
		if newOp.get('type') == 'csvLineIntoKnownValues':
			for baseOp in baseElement.findall('operation'):
				if baseOp.get('type') == 'csvLineIntoKnownValues':
					for newField in newOp.findall('newField'):
						isNew = True
						for baseField in baseOp.findall('newField'):
							if newField.text == baseField.text:
								isNew = False
								break
						if isNew:
							baseOp.append(newField)
