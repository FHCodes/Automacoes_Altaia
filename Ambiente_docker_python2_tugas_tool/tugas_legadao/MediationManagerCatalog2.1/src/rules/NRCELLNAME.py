__doc__ = \
	__version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

from lib.objects.column import column
from lib.functions import *
import xml.etree.ElementTree as ET

def process(unitDict, config):

	for ossId in unitDict.keys():
		unitObj = unitDict[ossId]

		if 'NRCellCU' in unitObj.attributes.keys() or 'NRCellDU' in unitObj.attributes.keys():

			columnObj = column()
			columnObj.create('NRCELL_NAME', 'NRCell_name', 'NRCell_name', 'NRCELL_NAME', 'NRCell_name', 'ID', 'VARCHAR2(256)', 'STRING', 'STRING', 'STRING', 0)
			unitObj.addAttribute('NRCELL_NAME', columnObj)

			opId = ('NRCellCU' if 'NRCellCU' in unitObj.attributes.keys() else 'NRCellDU')
			op = ET.Element('operation')
			op.set('type', 'copyValue')
			newField = ET.SubElement(op, 'newField')
			newField.text = 'NRCELL_NAME'

			unitObj.addOperation('item', opId, op)

		else:
			toCreate = False
			for tableId in unitObj.tables:
				tableObj = unitObj.tables[tableId]

				if 'NRCELLDU' in tableObj.bdcolnames or 'NRCELLDU' in tableObj.bdcolnames:

					if 'NRCELL_NAME' not in unitObj.bdcolnames:
						columnObj = column()
						columnObj.create('NRCELL_NAME', 'NRCell_name', 'NRCell_name', 'NRCELL_NAME', 'NRCell_name', 'ID', 'VARCHAR2(256)', 'STRING', 'STRING', 'STRING', 0)
						unitObj.addAttribute('NRCELL_NAME', columnObj)
						toCreate = True

			if toCreate:
				opId = ('NRCELLCU' if 'NRCELLCU' in tableObj.bdcolnames else 'NRCELLDU')
				op = ET.Element('operation')
				op.set('type', 'copyValue')
				newField = ET.SubElement(op, 'newField')
				newField.text = 'NRCELL_NAME'

				unitObj.addOperation('item', opId, op)

	return unitDict