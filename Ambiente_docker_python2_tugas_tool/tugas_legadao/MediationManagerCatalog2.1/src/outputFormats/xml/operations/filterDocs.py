__doc__ = \
	__version__ = '1.0'
__authors__ = ['Version 0.1: Marco Jeronimo <marco-a-jeronimo@alticelabs.com>']

# <operation type="filterDocs">
#	<filter by="regex" field="Granularity Period" pattern="60" />
# </operation>

from xml.etree.ElementTree import Element
import xml.etree.ElementTree as ET

def process(element, unitObj, config):

	eOperation = ET.SubElement(element, 'operation')
	eOperation.set('type', 'filterDocs')

	newField = ET.SubElement(eOperation, 'filter')
	newField.set('by', config['by'])
	newField.set('field', config['field'])
	newField.set('pattern', config['pattern'])