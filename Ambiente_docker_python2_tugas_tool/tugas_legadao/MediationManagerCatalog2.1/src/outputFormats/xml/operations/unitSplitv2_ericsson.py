__doc__ = \
	__version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

from xml.etree.ElementTree import Element
import xml.etree.ElementTree as ET

def process(element, unitObj, config):

	for tableId in unitObj.tables.keys():
		tableObj = unitObj.getTable(tableId)
		if tableObj.isStruct:
			unitObj.addStructDependencie(tableObj.typeId)

	dependencies = unitObj.structDependencies
	if dependencies != []:
		eOperation = ET.SubElement(element, 'operation')
		eOperation.set('type', 'unitSplitv2')

		field = ET.SubElement(eOperation, 'field')
		field.set('id', config['field'])

		for dep in dependencies:
			data = dep.split('_')
			regex = ET.SubElement(field, 'regex')
			regex.set('pattern', '.*(vsData|,)' + data[0] + '=[^,]+,' + data[1] + '.+$')
			#regex.set('pattern', '.*,?.*[vsData]?' + data[0] + '=[^,]+$')
			regex.set('newunit', dep)
