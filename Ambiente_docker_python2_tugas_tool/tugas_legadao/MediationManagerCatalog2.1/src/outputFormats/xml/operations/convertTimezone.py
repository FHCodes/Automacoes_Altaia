__doc__ = \
	__version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

from xml.etree.ElementTree import Element
import xml.etree.ElementTree as ET

def process(element, unitObj, config):
	"""
	convertTimezone":
	[
		{
			"field": "DATETIME",
			"newField": "DATETIME",
			"def":
				{
					"inTz": "UTC",
					"outTz": "Europe/Lisbon",
					"inPattern": "%Y-%m-%d %H:%M:%S",
					"outPattern": "%Y-%m-%d %H:%M:%S"
				}
		}
	]
	"""
	eOperation = ET.SubElement(element, 'operation')
	eOperation.set('type', 'convertTimezone')

	field = ET.SubElement(eOperation, 'field')
	field.text = config['field']

	newField = ET.SubElement(eOperation, 'newField')
	newField.text = config['newField']

	definition = ET.SubElement(eOperation, 'def')
	definition.set('in_tz', config['def']['inTz'])
	definition.set('out_tz', config['def']['outTz'])
	definition.set('in_pattern', config['def']['inPattern'])
	definition.set('out_pattern', config['def']['outPattern'])
