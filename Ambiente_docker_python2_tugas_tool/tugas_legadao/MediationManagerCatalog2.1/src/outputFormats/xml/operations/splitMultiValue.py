__doc__ = \
	__version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

from xml.etree.ElementTree import Element
import xml.etree.ElementTree as ET

def process(element, itemObj, config):

	if itemObj.multiplicity not in ['','Single', 0, '0']:
		eItem = ET.SubElement(element, 'item')
		eItem.set('id', itemObj.typeId)

		eOperation = ET.SubElement(eItem, 'operation')
		eOperation.set('compressed', str(itemObj.compressed))
		eOperation.set('type', 'splitMultiValue')

		eSplit = ET.SubElement(eOperation, 'split')

		eSplit.set('delimiter', config['delimiter'])
		for i in range(0, int(itemObj.multiplicity)):
			newField = ET.SubElement(eSplit, 'newField')
			newField.text = itemObj.typeId.upper() + 'SUB' + str(i)