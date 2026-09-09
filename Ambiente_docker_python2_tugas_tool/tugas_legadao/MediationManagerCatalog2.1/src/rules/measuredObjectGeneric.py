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
		value = list()
		value.append(re.sub(r' ', '', measuredObject))
		if ',' in value[0]:
			value = value[0].split(',')
		final = dict()
		
		for measuredObject in value:
			size = len(measuredObject.split(config['sepCharDoc']))
			if size not in final.keys():
				final[size] = list()
			final[size].append(measuredObject)

		for key in final.keys():
			for measuredObject in final[key]:
				if measuredObject is not '':
					
					newHierarchy = hierarchy()
					newHierarchy.create(measuredObject, list())
					
					hierarchyName = re.split(config['sepCharDoc'], measuredObject)
					hierarchyId = list()
					tmp = dict()

					for name in hierarchyName:
						if name not in tmp.keys():
							hierarchyId.append(name)
							tmp[name] = 1
						else:
							tmp[name] += 1
							hierarchyId.append(name + str(tmp[name]))

					for newFieldId in hierarchyId:
						position = hierarchyId.index(newFieldId)
						newHierarchy.addNewField(newFieldId)
						if newFieldId.upper() not in unitObj.attributes.keys():
							newField = column()
							newField.create(newFieldId, hierarchyName[position], validateUdn(newFieldId), validateSqlName(newFieldId), newFieldId, 'ID', 'VARCHAR2(256)', 'STRING', 'STRING', 'STRING', '')
							unitObj.addAttribute(newFieldId, newField)
					
					# Create pattern
					pattern = ''
					measuredObject = re.split(config['sepCharDoc'], measuredObject)
					#print measuredObject
					sep = ''
					for attributeId in newHierarchy.newFields:
						pattern += sep + measuredObject[0] + config['sepCharPattern'] + '(?P<' + attributeId.upper() + '>[^' + config['interChar'] + ']+?)'
						sep = config['interChar']
						measuredObject.pop(0)

					newHierarchy.pattern = pattern + '$'

					unitObj.addHierarchy(pattern, newHierarchy)
