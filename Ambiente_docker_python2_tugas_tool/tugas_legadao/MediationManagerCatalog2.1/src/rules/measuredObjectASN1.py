__doc__ = \
	__version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

import re
from lib.objects.column import column
from lib.objects.hierarchy import hierarchy
from lib.functions import *

def process(unitDict, config):
	for unitId in unitDict.keys():
		unitObj = unitDict[unitId]
		measuredObject = re.sub(config['regex'], '', unitObj.measuredObject)
		value = re.sub(r' ', '', measuredObject).split(',')
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

					hierarchyName = measuredObject.split(config['sepCharDoc'])
					hierarchyId = list()
					tmp = dict()

					for name in hierarchyName:
						if name not in tmp.keys():
							hierarchyId.append(name)
							tmp[name] = 1
						else:
							tmp[name] += 1
							hierarchyId.append(name + str(tmp[name]))

					for attributeId in hierarchyId:
						position = hierarchyId.index(attributeId)
						attribute = column()
						attribute.create(attributeId, hierarchyName[position], validateUdn(attributeId), validateSqlName(attributeId), attributeId, 'ID', 'VARCHAR2(256)', 'STRING', 'STRING', 'STRING', '')
						newHierarchy.addNewField(attributeId)
						unitObj.addAttribute(attributeId, attribute)

					# Create pattern
					pattern = ''
					#measuredObject = measuredObject.split(config['sepCharDoc'])
					# print newHierarchy.name
					i = 0
					for attributeId in newHierarchy.newFields:
						pattern += config['sepCharPattern'] + '(?P<' + attributeId + '>.+?)'
						i += 1

					newHierarchy.pattern = pattern + '$'

					unitObj.addHierarchy(measuredObject, newHierarchy)
