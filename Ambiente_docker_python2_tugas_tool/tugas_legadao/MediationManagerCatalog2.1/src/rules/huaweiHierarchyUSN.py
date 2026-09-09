__doc__ = \
__version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

import re
from lib.objects.column import column
from lib.objects.hierarchy import hierarchy
from lib.functions import *
from collections import OrderedDict

def process(unitDict, config):
	for ossId in unitDict.keys():
		unitObj = unitDict[ossId]
		unitHierarchy = None
		measuredObject = re.sub(config['regex'], '', unitObj.measuredObject)
		mList = re.split(r'\r|\n|;', measuredObject)
		objNameList = list()
		for baseMeasuredObject in mList:
			measuredObject = re.sub(r',\s|/\s', ',', baseMeasuredObject)
			newHierarchy = hierarchy()
			newHierarchy.create(measuredObject, list())

			measObjs = (re.sub(r'[/|,| ]', '', measuredObject)).strip().split('?')
			dataList = list()
			dataList.append(config['startField'])
			objReps = OrderedDict(object_pairs_hook=OrderedDict)
			objReps[config['startField']] = 1

			for obj in measObjs:
				if obj != '':
					objIdList = (re.sub('\.|=|_|-|\(|\)|\+', '', obj)).split(':')
					if objIdList[-1] == '':
						del objIdList[-1]
					objId = objIdList[-1]

					for tKey in objIdList[:-2]:
						if tKey != objIdList[-2]:
							objId = ('{0}{1}').format(tKey, objId)

					if objId not in objReps.keys():
						objReps[objId] = 1
					else:
						objReps[objId] += 1
						objId = objId + str(objReps[objId])

					if objId not in objNameList:
						objNameList.append(objId)
					dataList.append(objId)

			pattern = ''
			measuredObject = re.split(r'\?*', re.sub(r', ', ',\s*', baseMeasuredObject))
			del measuredObject[-1]

			for preFix in measuredObject:
				preFix = correctPrefix(preFix)
				newField = column()
				newField.create(dataList[0].upper(), dataList[0], validateUdn(dataList[0]), validateSqlName(dataList[0]), dataList[0], 'ID', 'VARCHAR2(256)', 'STRING', 'STRING', '', '')
				pattern += preFix + '(?P<' + dataList[0].upper() + '>.+?)'
				unitObj.addAttribute(dataList[0].upper(), newField)
				newHierarchy.addNewField(dataList[0])
				del dataList[0]

			newHierarchy.pattern = pattern + '$'

			unitObj.addHierarchy(baseMeasuredObject, newHierarchy)

		unitObj.measuredObject = re.sub(r'\r|\n', '#', unitObj.measuredObject)


def correctPrefix(field):
	newField = ''
	for index, value in reversed(list(enumerate(field))):
		newField = '{0}{1}'.format(('\\' + value if re.match('\(|\)', value) else value), newField)
	return newField
