__doc__ = \
	__version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

from xml.etree.ElementTree import Element
import xml.etree.cElementTree as ET

# #
# Given an constant data and regex
# #
def process(element, unitObj, config):

	if unitObj.hierarchyList is not None and len(unitObj.hierarchyList) > 0 and unitObj.createHierarchy:
		column = ET.Element('item')
		element.append(column)
		column.set('id', config['field'])
		operation = ET.SubElement(column, 'operation')
		operation.set('type', 'applyRegex')

		regex = ET.SubElement(operation, 'regex')
		regex.set('pattern', config['pattern'])
		for key in config['newFields']:
			newField = ET.SubElement(regex, 'newField')
			newField.text = key.upper()
