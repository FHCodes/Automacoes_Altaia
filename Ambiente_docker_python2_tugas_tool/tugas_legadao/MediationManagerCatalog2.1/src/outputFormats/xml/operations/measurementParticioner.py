__doc__ = \
	__version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

from xml.etree.ElementTree import Element
import xml.etree.ElementTree as ET

def process(element, unitObj, config):
	try:
		operation = unitObj.getOperation('unit', 'measurementPartition')
	except:
		operation = None

	if operation != None:
		eOperation = ET.SubElement(element, 'operation')
		eOperation.set('type', 'measurementPartition')

		for listBlock in operation:
			listBlock = listBlock['def'][0]
			for measurement in listBlock['measurements']:
				eMeasurement = ET.SubElement(eOperation, 'measurement')
				eMeasurement.text = measurement
			for sharedField in listBlock['sharedFields']:
				eSharedField = ET.SubElement(eOperation, 'sharedField')
				eSharedField.text = sharedField
		return unitObj

	eOperation = ET.SubElement(element, 'operation')
	eOperation.set('type', 'measurementPartition')

	for listBlock in config['def']:
		for measurement in listBlock['measurements']:
			eMeasurement = ET.SubElement(eOperation, 'measurement')
			eMeasurement.text = measurement

		for sharedField in listBlock['sharedFields']:
			eSharedField = ET.SubElement(eOperation, 'sharedField')
			eSharedField.text = sharedField

	return unitObj
