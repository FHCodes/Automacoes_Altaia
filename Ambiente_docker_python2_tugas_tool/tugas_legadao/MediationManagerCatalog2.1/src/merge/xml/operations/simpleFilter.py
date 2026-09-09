__doc__ = \
	__version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

from lib.Logger import Logger

def process(baseElement, newElement):
	logger = Logger('operationsMerge').get()

	for newOp in newElement.findall('operation'):
		if newOp.get('type') == 'simpleFilter':
			for baseOp in baseElement.findall('operation'):
				if baseOp.get('type') == 'simpleFilter':
					for newAllow in newOp.findall('allow'):
						isNew = True
						for baseAllow in baseOp.findall('allow'):
							if newAllow.text == baseAllow.text:
								isNew = False
						if isNew:
							baseOp.append(newAllow)
