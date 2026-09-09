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
		if unitObj.measuredObject == '':
			continue
		measuredObject = re.sub(config['regex'], '', unitObj.measuredObject)
		measuredObject = re.sub(r' ', '', measuredObject)
		tmp = measuredObject.split(',')
		hierarchyList = list()
		for t in tmp:
			if t not in hierarchyList:
				for hi in hierarchyList:
					if len(t.split(config['sepCharDoc'])) >= len(hi.split(config['sepCharDoc'])):
						hierarchyList.insert(hierarchyList.index(hi), t)
						break
				if t not in hierarchyList:
					hierarchyList.insert(-1, t)

		for hierarchyStr in hierarchyList:
			newHierarchy = hierarchy()
			newHierarchy.create(hierarchyStr, list())

			if 'startText' in config:
				hierarchyStr = config['startText'] + hierarchyStr

			attributeList = hierarchyStr.split(config['sepCharDoc'])
			for attributeId in attributeList:
				newField = column()
				newField.create(attributeId, attributeId, validateUdn(attributeId), validateSqlName(attributeId), attributeId, 'ID', 'VARCHAR2(256)', 'STRING', 'STRING', '', '')
				newHierarchy.addNewField(attributeId)
				#if attributeId not in unitObj.attributes.keys():
				#	unitObj.addAttribute(attributeId, newField)

			# Create pattern
			pattern = ''
			# print newHierarchy.name
			for attributeId in newHierarchy.newFields:
				pattern += ('' if pattern == '' else config['sepCharPattern']) + '(?P<' + attributeId.upper() + '>[^,]+?)'

			pattern = pattern + '$'
			newHierarchy.pattern = pattern
			unitObj.addHierarchy(hierarchyStr, newHierarchy)
