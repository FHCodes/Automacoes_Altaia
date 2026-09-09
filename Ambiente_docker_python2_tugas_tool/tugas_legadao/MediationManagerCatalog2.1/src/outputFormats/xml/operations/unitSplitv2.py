__doc__ = \
	__version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

from xml.etree.ElementTree import Element
import xml.etree.ElementTree as ET

def process(element, unitObj, config):

	eOperation = ET.SubElement(element, 'operation')
	eOperation.set('type', 'unitSplitv2')

	field = ET.SubElement(eOperation, 'field')
	field.set('id', config['field'])

	for data in config['regex']:
		regex = ET.SubElement(field, 'regex')
		regex.set('pattern', data['pattern'])
		regex.set('newunit', data['newunit'])
