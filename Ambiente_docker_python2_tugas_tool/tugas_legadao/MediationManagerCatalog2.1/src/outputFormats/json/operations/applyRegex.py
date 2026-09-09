__doc__ = \
	__version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

from xml.etree.ElementTree import Element
import xml.etree.ElementTree as ET
from collections import OrderedDict

def process(unit, unitObj, config):

	if unitObj.hierarchyList is not None and unitObj.createHierarchy:
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

		hList = dict()
		for hierarchyId in unitObj.hierarchyList.keys():
			element = OrderedDict()
			hierarchyObj = unitObj.hierarchyList[hierarchyId]
			element['pattern'] = hierarchyObj.pattern
			element['newFields'] = list()
			size = len(hierarchyObj.newFields)
			for hierNewField in hierarchyObj.newFields:
				element['newFields'].append(hierNewField.upper())

			if size not in hList.keys():
				hList[size] = list()
			hList[size].append(element)

		for pos in sorted(hList.keys()):
			for regex in hList[pos]:
				operation['def'].insert(0, regex)

		if operation['def'] == list():
			return unit

		try:
			unit['measItems'] = unit['measItems'] + measItems
		except:
			unit['measItems'] = measItems

	return unit