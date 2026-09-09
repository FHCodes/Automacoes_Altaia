__doc__ = \
__version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

import re
from lib.objects.column import column
from lib.objects.hierarchy import hierarchy
from lib.functions import *

def process(unitDict,config):
	for ossId in unitDict.keys():
		unitObj = unitDict[ossId]

		measuredObject = re.sub(r' ', '', unitObj.measuredObject)
		measuredObject = re.sub(r',', '-', unitObj.measuredObject)
		createHierarchy(unitObj, config, measuredObject)
		#tmpHierarchy.typeId = gerarPattern(tmpHierarchy.typeId, tmpHierarchy.newFields, config['sepCharDoc'])

def createHierarchy(unitObj, config, measuredObject):

		newHierarchy = hierarchy()
		newHierarchy.create(measuredObject, list())

		if 'regex' in config:
			measuredObject = re.sub(config['regex'], '', measuredObject)
			newHierarchy.typeId = measuredObject
		measuredObject = re.sub('\(', ',', measuredObject)
		if '(' in measuredObject:
			tmp = measuredObject.split('(')
			measuredObject = removeDuplicates(tmp[0], config['sepCharDoc']) + config['sepCharDoc'] + transformDuplicates(tmp[1], config['sepCharDoc'])
		else:
			measuredObject = removeDuplicates(measuredObject, config['sepCharDoc'])


		hierarchyName = measuredObject.split(config['sepCharDoc'])
		hierarchyId = list()
		tmp = dict()

		for name in hierarchyName:
			if name not in tmp.keys():
				hierarchyId.append(name)
				tmp[name] = 1
			else:
				tmp[name] += 1
				hierarchyId.append(name+str(tmp[name]))

		#Create pattern
		pattern = ''
		sep = ''
		measuredObject = (newHierarchy.typeId.replace(' ', '').replace(',', '(').replace(')', '').replace('(', '-,(.+?)')).split('-')

		for attributeId in hierarchyId:
			position = hierarchyId.index(attributeId)
			newField = column()

			newField.create(attributeId, hierarchyName[position], validateUdn(attributeId), validateSqlName(attributeId), attributeId, 'ID', 'VARCHAR2(256)', 'STRING', 'STRING', 'STRING', '')

			while not measuredObject[0].upper().endswith(attributeId.upper()):
				del measuredObject[0]
				if len(measuredObject) == 0:
					break
			if len(measuredObject) > 0:
				pattern += sep + measuredObject[0] + config['sepCharPattern'] + '(?P<' + attributeId.upper() + '>[^' + config['interChar'] + ']+?)'
				sep = config['interChar']
				del measuredObject[0]

			newHierarchy.addNewField(attributeId)
			unitObj.addAttribute(attributeId, newField)

		newHierarchy.pattern = pattern + '$'

		unitObj.addHierarchy(pattern, newHierarchy)

def removeDuplicates(measuredObject,sepChar):
	measuredObject = (re.sub(r',', sepChar, measuredObject)).split(sepChar)
	tmp = ''
	tmpList = list()
	for attr in measuredObject:
		if attr in tmpList:
			continue

		tmp += attr + sepChar
		tmpList.append(attr)

	return tmp[:-len(sepChar)]

def transformDuplicates(measuredObject,sepChar):
	measuredObject = re.sub(r'(,.*=|\))', '', measuredObject)
	return re.sub(r'\(|,', sepChar, measuredObject)

#deprecated
def gerarPattern(hierarchy,field,sepChar):

	if '(' in hierarchy:
		data = hierarchy.replace(')', '').split('(')
		AllParts = data[0].split(sepChar)
		afterPartList = data[1].split(',')
		for part in afterPartList:
			brokenPart = part.split(sepChar)
			AllParts.append(',(.+?)' + brokenPart[0])
			for index in range(1,len(brokenPart)):
				AllParts.append(brokenPart[index])
	else:
		AllParts = hierarchy.split(sepChar)

	pattern = ''
	index = 0
	sep = ''
	while field is not None:
		if AllParts[index].startswith(',(.+?)'):
			pattern += AllParts[index] + '-(?P<' + field.typeId + '>.+?)'
		else:
			pattern += sep + AllParts[index] + '-(?P<' + field.typeId + '>.+?)'
		sep = '/'
		index += 1
		field = field.getNext()

	return pattern + '$'
