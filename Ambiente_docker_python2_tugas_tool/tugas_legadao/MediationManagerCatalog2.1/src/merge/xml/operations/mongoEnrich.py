__doc__ = \
	__version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

from lib.Logger import Logger

def process(baseElement, newElement):
	logger = Logger('operationsMerge').get()

	for newOp in newElement.findall('operation'):
		if newOp.get('type') == 'mongoEnrich':
			isNewCollection = True
			for baseOp in baseElement.findall('operation'):
				if baseOp.get('type') == 'mongoEnrich':
					if newOp.get('collection') == baseOp.get('collection'):
						isNewCollection = False
						for newSource in newOp.findall('source'):
							isNewSource = True
							for baseSource in baseOp.findall('source'):
								if newSource.get('name') == baseSource.get('name'):
									isNewSource = False
									for newCorrKey in newSource.findall('corrKey'):
										isNewCorrKey = True
										for baseCorrKey in baseSource.findall('corrKey'):
											if newCorrKey.text == baseCorrKey.text:
												isNewCorrKey = False
										if isNewCorrKey:
											logger.warning('  * [mongoEnrich][{:5s}] differs between base Catalog and new Catalog in the unit: {:3s} *'.format('corrKey', baseElement.get('id')))

									for newField in newSource.findall('newField'):
										isNewField = True
										for baseField in baseSource.findall('newField'):
											if newField.text == baseField.text:
												isNewField = False
										if isNewField:
											baseSource.append(newField)
							if isNewSource:
								baseOp.append(newSource)
			if isNewCollection:
				baseElement.append(newOp)
