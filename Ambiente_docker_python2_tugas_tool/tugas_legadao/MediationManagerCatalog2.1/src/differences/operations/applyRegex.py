__doc__ = \
	__version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

from xml.etree.ElementTree import Element
import xml.etree.ElementTree as ET

def process(element, unitObj, config):

	if unitObj.hierarchyList is not None and unitObj.createHierarchy:
		column = ET.SubElement(element, 'item')
		column.set('id', config['field'])
		operation = ET.SubElement(column, 'operation')
		operation.set('type', 'applyRegex')

		hList = dict()
		for hierarchyId in unitObj.hierarchyList.keys():
			hierarchyObj = unitObj.hierarchyList[hierarchyId]
			regex = ET.Element('regex')
			regex.set('pattern', hierarchyObj.pattern)
			size = len(hierarchyObj.newFields)
			for hierNewField in hierarchyObj.newFields:
				newField = ET.SubElement(regex, 'newField')
				newField.text = hierNewField

			if size not in hList.keys():
				hList[size] = list()
			hList[size].append(regex)

		for pos in reversed(hList.keys()):
			for regex in hList[pos]:
				operation.insert(0, regex)
