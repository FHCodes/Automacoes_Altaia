__doc__ = \
	__version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

from xml.etree.ElementTree import Element
import xml.etree.ElementTree as ET

def process(unit, opJson, config):
	operations = dict()
	try:
		operations = unit['operations']
	except:
		pass

	operDef = None
	for oper in operations:
		if oper['type'] == 'measurementPartition':
			operDef = oper['def']
	unit['operations'].append(opJson)
	return unit
