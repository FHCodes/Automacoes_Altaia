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
		mList = re.split(r'\r|\n', measuredObject)
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
					tmpObj = obj.replace('=', '').split(':')
					if len(tmpObj) == 1:
						if tmpObj[0] == '':
							objId = dataList[-1]
						else:
							objId = tmpObj[0].replace(' ', '')
					else:
						while len(tmpObj) > 0:
							if tmpObj[-1] != '':
								break
							del tmpObj[-1]
						if len(tmpObj) == 0:
							objId = objReps.keys()[-1]
						else:
							objId = tmpObj[-1].replace(' ', '')

					if objId.upper() not in objReps.keys():
						objReps[objId.upper()] = 1
					else:
						objReps[objId.upper()] += 1
						objId = objId + str(objReps[objId.upper()])

					if objId not in objNameList:
						objNameList.append(objId)
					dataList.append(objId)

			pattern = ''
			measuredObject = re.split(r'\?*', re.sub(r', ', ',\s*', re.sub(r'\:\?', '=?', baseMeasuredObject)))
			del measuredObject[-1]

			for preFix in measuredObject:
				newField = column()
				newField.create(dataList[0], dataList[0], validateUdn(dataList[0]), validateSqlName(dataList[0]), dataList[0], 'ID', 'VARCHAR2(256)', 'STRING', 'STRING', '', '')
				pattern += preFix + '(?P<' + dataList[0] + '>.+?)'
				unitObj.addAttribute(dataList[0], newField)
				newHierarchy.addNewField(dataList[0])
				del dataList[0]

			newHierarchy.pattern = pattern + '$'

			unitObj.addHierarchy(baseMeasuredObject, newHierarchy)

		unitObj.measuredObject = re.sub(r'\r|\n', '#', unitObj.measuredObject)
