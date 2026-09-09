__doc__ = \
	__version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

from xml.etree.ElementTree import Element
import xml.etree.ElementTree as ET

def process(element, unitObj, config):

	if config['bdcolname'] in unitObj.bdcolnames:
		eOperation = ET.SubElement(element, 'operation')
		eOperation.set('type', 'fixedValue')

		newField = ET.SubElement(eOperation, 'newField')
		newField.set('value', config['value'])
		newField.text = config['newFieldId']