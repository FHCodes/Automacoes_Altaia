__doc__ = \
__version__ = '1.2'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>'
               'Version 0.2: Gil Martins <gil-l-martins@alticelabs.com>']

import re
from lib.objects.column import column
from lib.objects.hierarchy import hierarchy
from lib.functions import *
from collections import OrderedDict
from lib.Logger import Logger

def process(unitDict, config):
	for ossId in unitDict.keys():
		unitObj = unitDict[ossId]
		
		if unitObj.measuredObject == '' or unitObj.measuredObject is None:
			logger = Logger('processLogger').get()
			logger.error("  * {:s}{:s} *".format('Missing hierarchy in unit ', ossId))
			continue
		
		hierarchyList = re.split(r'\r|\n', unitObj.measuredObject)

		for measuredObject in hierarchyList:
			newHierarchy = hierarchy()
			newHierarchy.create(measuredObject, list())
			measuredObject = re.sub(r',\s', ',\s', measuredObject)

			measuredObjectBlock = measuredObject.split('/')

			pattern = '(?P<' + config['startField'] + '>.+?)'
			newField = column()
			newField.create(config['startField'], config['startField'], validateUdn(config['startField']), validateSqlName(config['startField']), config['startField'], 'ID', 'VARCHAR2(256)', 'STRING', 'STRING', '', '')
			unitObj.addAttribute(config['startField'], newField)
			newHierarchy.addNewField(config['startField'])
			del measuredObjectBlock[0]
			elementDict = dict()
			bckUp = ''
			for block in measuredObjectBlock:
				blockElement = block.split('?')
				parentId = ''
				pattern += '/'
				del blockElement[-1]
				if ':' in blockElement[0]:
					parentId = re.sub(r'\\|\/| |\<|\>|-', '', blockElement[0].split(':')[0])
				for element in blockElement:
					#elementId = parentId + re.sub(r'^.*:|^.*,(\\s)| |=|-|\.', '', element)
					#elementId = re.sub(r'^.*:|^.*,(\\s)| |=|-|\.', '', element)
					#print element
					elementId = re.sub(r'^.*:|^.*,(\\s)*| |=|-|\.', '', element)
					if elementId == '' and bckUp != '':
						elementId = bckUp
					elif ',' in elementId:
						v = elementId.split(',')
						bckUp = v[1]
						elementId = v[0]
					elif elementId == '':
						#print parentId
						if ',' in parentId:
							v = parentId.split(',')
							bckUp = v[1]
							elementId = v[0]
						else:
							elementId = parentId
					if elementId.upper() in elementDict.keys():
						elementDict[elementId.upper()] += 1
						elementId = elementId + '_' + str(elementDict[elementId.upper()])
					else:
						elementDict[elementId.upper()] = 1
					newField = column()
					newField.create(elementId, elementId, elementId, validateSqlName(elementId), elementId, 'ID', 'VARCHAR2(256)', 'STRING', 'STRING', '', '')
					
					# for pattern, add whitespace control (0 or more) if element starts with comma: ',<element>' -> ',\s*<element>'
					if element.startswith(', '):
						element = re.sub(', ', r',\s*', element, 1)
					elif element.startswith(','):
						element = re.sub(',', r',\s*', element, 1)
						
					pattern += element + '(?P<' + elementId + '>.*?)'
					newHierarchy.addNewField(elementId)
					unitObj.addAttribute(elementId, newField)

			newHierarchy.pattern = '^' + pattern + '$'
			unitObj.addHierarchy(measuredObject, newHierarchy)
			unitObj.measuredObject = re.sub(r'\r|\n', '#', unitObj.measuredObject)
