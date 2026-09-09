__doc__ = \
	__version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

import re
from lib.objects.column import column
from lib.objects.hierarchy import hierarchy
from lib.functions import *

def process(unitDict, config):
	for ossId in unitDict.keys():
		unitObj = unitDict[ossId]
		measuredObject = re.sub(config['regex'], '', unitObj.measuredObject)
		if measuredObject == '':
			continue
		measObjList = re.sub(r' ', '', measuredObject).split(',')
		measObjBySize = dict()

		convertId = list()

		for measuredObject in measObjList:
			size = len(measuredObject.split(config['sepCharDoc']))
			if size not in measObjBySize.keys():
				measObjBySize[size] = list()
			measObjBySize[size].append(measuredObject)
			for attr in measuredObject.split(config['sepCharDoc']):
				try:
					if attr in unitObj.attributes:
						convertId.append(attr)
						unitObj.update('BDCOLNAME', [attr, attr + 'CM'])
						unitObj.attributes[attr].update('UDN', attr + 'CM')
					elif attr.upper() in unitObj.attributes:
						convertId.append(attr)
						unitObj.update('BDCOLNAME', [attr.upper(), attr + 'CM'])
						unitObj.attributes[attr.upper()].update('UDN', attr + 'CM')
				except:
					pass
				else:
					for tableId in unitObj.tables.keys():
						tableObj = unitObj.getTable(tableId)
						try:
							if attr in tableObj.counters.keys():
								convertId.append(attr)
								tableObj.update('BDCOLNAME', [attr, attr + 'CM'])
								tableObj.counters[attr].update('UDN', attr + 'CM')
							elif attr.upper() in tableObj.counters.keys():
								convertId.append(attr)
								tableObj.update('BDCOLNAME', [attr.upper(), attr + 'CM'])
								tableObj.counters[attr.upper()].update('UDN', attr + 'CM')
						except:
							pass

		for key in measObjBySize.keys():
			for measuredObject in measObjBySize[key]:
				if 'startText' in config:
					measuredObject = config['startText'] + measuredObject
				if measuredObject is not '':
					
					newHierarchy = hierarchy()
					newHierarchy.create(measuredObject, list())
					
					hierarchyName = measuredObject.split(config['sepCharDoc'])
					hierarchyId = list()
					hierarchyBdcolname = dict()
					tmp = dict()
					
					for name in hierarchyName:
						#Verify if there is another field with the same id
						bdcolname = name
						if name in convertId:
							#bdcolname = name + 'CM'
							name = name + 'FDN'

						if name not in tmp.keys():
							hierarchyId.append(name)
							hierarchyBdcolname[name] = bdcolname
							tmp[name] = 1
						else:
							tmp[name] += 1
							hierarchyId.append(name + str(tmp[name]))
							hierarchyBdcolname[name] = bdcolname + str(tmp[name])

					# Create pattern
					pattern = '^.*'
					sep = ''
					for attributeId in hierarchyId:
						#position = hierarchyId.index(attributeId)
						sColumn = column()
						sColumn.create(attributeId, attributeId, validateUdn(hierarchyBdcolname[attributeId]), validateSqlName(hierarchyBdcolname[attributeId]), attributeId, 'ID', 'VARCHAR2(256)', 'STRING', 'STRING', 'STRING', '')
						unitObj.addAttribute(attributeId, sColumn)
						newHierarchy.addNewField(attributeId)

						pattern += sep + hierarchyName.pop(0) + config['sepCharPattern'] + '(?P<' + attributeId.upper() + '>.+?)'
						sep = config['interChar']

					newHierarchy.pattern = pattern + '$'

					unitObj.addHierarchy(measuredObject, newHierarchy)
