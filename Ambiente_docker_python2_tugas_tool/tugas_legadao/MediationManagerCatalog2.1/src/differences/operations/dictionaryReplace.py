__doc__ = \
	__version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

from xml.etree.ElementTree import Element
import xml.etree.ElementTree as ET

def process(element, itemObj, config):

	if itemObj.typeId == config['field']:
		eItem = ET.SubElement(element, 'item')
		eItem.set('id', itemObj.typeId)

		eOperation = ET.SubElement(eItem, 'operation')
		eOperation.set('type', 'dictionaryReplace')

		for item in config['options']:
			nItem = ET.SubElement(eOperation, 'item')
			key = ET.SubElement(nItem, 'key')
			key.text = item['key']
			value = ET.SubElement(nItem, 'value')
			value.text = item['value']