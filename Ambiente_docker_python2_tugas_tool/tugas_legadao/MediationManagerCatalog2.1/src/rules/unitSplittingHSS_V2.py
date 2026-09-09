__doc__ = \
	__version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

from lib.functions import validateSqlName
from lib.objects.table import table
from lib.objects.unit import unit
import xml.etree.ElementTree as ET

# #
# Adds a prefix in a field
# #
def process(unitDict, config):
	if not config['active']:
		return

	unitList = unitDict.keys()

	for ossId in unitList:
		unitObj = unitDict[ossId]
		
		if config['key'] in unitObj.measuredObject:
			newUnitObj = unit()
			newUnitObj.create(ossId, ossId, unitObj.get('NAME'), '{0}'.format(unitObj.desc), '')
	
			newId = '{0}_{1}'.format(ossId, config['key'])
			unitObj.update('OSSID', newId.upper())
			unitObj.update('ID', newId.upper())
			unitObj.update('NAME', '{0}_{1}'.format(unitObj.get('NAME'), config['key'].upper()))
			unitObj.update('DESC', '{0} {1}'.format(unitObj.desc, config['key']))
	
			for tableId in unitObj.tables:
				tableObj = unitObj.getTable(tableId)
				newTableObj = table()
				newTableObj.create(tableId, tableId, tableObj.sqlName, tableObj.get('UDN'))
				newUnitObj.addTable(tableId, newTableObj)
	
				tableObj.update('UDN', '{0}_{1}'.format(tableObj.get('UDN'), config['regex']))
				tableObj.update('TABLENAME', '{0}_{1}'.format(tableObj.sqlName, config['key'].upper()))
				tableObj.update('ID', newId)
				tableObj.update('OSSID', newId)
			
			
			unitSplit = ET.Element('operation')
			unitSplit.set('type', 'unitSplitv2')
			field = ET.SubElement(unitSplit, 'field')
			field.set('id', 'MEASUREDOBJECTID')
			reg = ET.SubElement(field, 'regex')
			reg.set('newunit', newId.upper())
			reg.set('pattern', '^.*/{0}-.*'.format(config['regex']))
			newUnitObj.addOperation('unit', 'unitSplitv2', unitSplit)
			
			tmp = unitObj
			unitDict[ossId] = newUnitObj
			unitDict[newId.upper()] = tmp
			
			