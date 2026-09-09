__doc__ = \
	__version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

from xml.etree.ElementTree import Element
import xml.etree.ElementTree as ET
from collections import OrderedDict

def process(unit, unitObj, config):

	if unitObj.createHierarchy:
		measItems = list()

		measItem = None
		for measItem in measItems:
			if measItem['id'] == config['field']:
				break

		if measItem == None:
			measItem = OrderedDict()
			measItem['id'] = config['field'].upper()
			measItem['operations'] = list()
			measItems.append(measItem)

		operation = None
		for operation in measItem['operations']:
			if operation['type'] == 'applyRegex':
				break

		if operation == None:
			operation = OrderedDict()
			operation['type'] = 'applyRegex'
			operation['def'] = list()
			measItem['operations'].append(operation)

		element = OrderedDict()
		element['pattern'] = config['pattern']
		element['newFields'] = config['newFields']
		operation['def'].insert(0, element)

		if operation['def'] == list():
			return unit

		try:
			unit['measItems'] = unit['measItems'] + measItems
		except:
			unit['measItems'] = measItems

	return unit