__doc__ = \
	__version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

from lib.functions import nameRedutor
import json
from lib.objects.column import column
from lib.functions import *

def process(unitDict, config):

	for unitId in unitDict.keys():
		isStruct = False
		unitObj = unitDict[unitId]
		for tableId in unitObj.tables.keys():
			if unitObj.tables[tableId].isStruct:
				isStruct = True
				break
		for hierKey in unitObj.hierarchyList.keys():
			hierObj = unitObj.hierarchyList[hierKey]
			listOfFields = (hierObj.newFields[:-1] if isStruct else hierObj.newFields)
			for fieldId in listOfFields:
				newFieldId = '{0}_NAME'.format(fieldId)
				if newFieldId not in unitObj.attributes.keys():
					newField = column()
					newField.create(newFieldId, newFieldId, newFieldId, validateSqlName(newFieldId), newFieldId, 'ID', 'VARCHAR2(256)', 'STRING', 'STRING', 'STRING', '')
					unitObj.addAttribute(newFieldId, newField)
