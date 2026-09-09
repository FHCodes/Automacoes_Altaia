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
		if config['regex'] != '':
			measuredObject = re.sub(config['regex'], '', unitObj.measuredObject)

		if config['3gpp']:
			createHierarchy3GPP(unitObj, config, measuredObject)
		if config['omes']:
			createHierarchyOMES(unitObj, config, measuredObject)

def createHierarchy3GPP(unitObj, config, measuredObject):

		newHierarchy = hierarchy()
		newHierarchy.create(measuredObject, list())
		measuredObject = re.sub(r'\(PLMN-|,PLMN-', ',(.+?)', measuredObject.replace(')', ''))
		measuredObjectList = re.findall(r'(\)|^|-)+([^-,)]*)', measuredObject)
		#measuredObjectList = cleanList(measuredObjectList)

		measuredObject = re.split(r'-|,', measuredObject)
		pattern = '^.*'
		sep = ''
		for _x, attributeId in measuredObjectList:
			#print attributeId
			newField = column()
			newField.create(attributeId.upper(), attributeId, attributeId, validateSqlName(attributeId.upper()), attributeId, 'ID', 'VARCHAR2(256)', 'STRING', 'STRING', 'STRING', '')

			pattern += (',' if measuredObject[0].startswith('(') else sep) + measuredObject[0] + config['sepCharPattern'] + '(?P<' + attributeId.upper() + '>[^' + config['interChar'] + ']+?)'
			del measuredObject[0]
			sep = config['interChar']

			newHierarchy.addNewField(attributeId)
			unitObj.addAttribute(attributeId, newField)

		newHierarchy.pattern = pattern + '$'

		unitObj.addHierarchy(pattern, newHierarchy)


def createHierarchyOMES(unitObj, config, measuredObject):

		newHierarchy = hierarchy()
		newHierarchy.create(measuredObject, list())
		measuredObject = re.sub(r'\(PLMN-|,PLMN-', '-', measuredObject.replace(')', ''))
		measuredObjectList = re.findall(r'(\)|^|-)+([^-,)]*)', measuredObject)
		#measuredObjectList = cleanList(measuredObjectList)

		measuredObject = re.split(r'-|,', measuredObject)
		pattern = '^.*'
		sep = ''
		for _x, attributeId in measuredObjectList:
			#print attributeId
			newField = column()
			newField.create(attributeId.upper(), attributeId, attributeId, validateSqlName(attributeId.upper()), attributeId, 'ID', 'VARCHAR2(256)', 'STRING', 'STRING', 'STRING', '')

			pattern += (',' if measuredObject[0].startswith('(') else sep) + measuredObject[0] + config['sepCharPattern'] + '(?P<' + attributeId.upper() + '>[^' + config['interChar'] + ']+?)'
			del measuredObject[0]
			sep = config['interChar']

			newHierarchy.addNewField(attributeId.upper())
			if attributeId.upper() not in unitObj.attributes:
				unitObj.addAttribute(attributeId.upper(), newField)

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

def cleanList(measuredObject):
	newList = list()
	state = False
	for key in measuredObject:
		if state:
			newList.append(key)
		state = not state
	return newList