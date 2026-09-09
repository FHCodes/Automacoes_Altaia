__doc__ = \
	__version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

import re
from lib.objects.column import column
from lib.objects.hierarchy import hierarchy
from lib.functions import *


# Example #usecase:
# RACK=(#),SHELF=1(#),SLOT=(#),PORT=(#),ONU=(#),GPON ONU Ethernet Port=(#)

def process(unitDict, config):
	for ossId in unitDict.keys():
		unitObj = unitDict[ossId]
		measuredObject = re.sub(config['regex'], '', unitObj.measuredObject)

		if measuredObject == '':
			continue

		value = list()
		# x = re.sub(r' ', '', measuredObject).split(',')
		x = measuredObject.split(',')
		for v in x:
			if v not in value:
				value.append(v)
		final = dict()
		
		# Example #usecase:
		# value = ['RACK=(#)', SHELF=1(#), ...]

		for measuredObject in value:
			size = len(measuredObject.split('='))
			if size not in final.keys():
				final[size] = list()
			final[size].append(measuredObject)

			# Example #usecase:
			# final = { '2':['RACK=(#)', 'SHELF=1(#)', ...] }

		# to save correct names for pattern
		saveIdForPattern = list()

		for key in final.keys():

			# Creating hierarchy
			newHierarchy = hierarchy()
			newHierarchy.create('', list())  # pattern, lista de hierarquias

			for measuredObject in final[key]:
				if measuredObject is not '':

					# Example #usecase:
					# 'RACK=(#)'

					hierarchyName = re.split('=', measuredObject)
					hierarchyId = list()
					tmp = dict()

					for name in hierarchyName:
						if name not in tmp.keys():
							hierarchyId.append(name)
							tmp[name] = 1
						else:
							tmp[name] += 1
							hierarchyId.append(name + str(tmp[name]))

					# Example #usecase:
					# hierarchyName = ['RACK','(#)']
					# hierarchyId = ['RACK','(#)']

					# Adding fields to the hierarchy : new columns to be generated -> 'position%2==0' to jump the unwanted char(s)
					for newFieldId in hierarchyId:
						position = hierarchyId.index(newFieldId)
						if position % 2 == 0:
							saveIdForPattern.append(newFieldId)
							newFieldId = newFieldId.upper()  # RACK
							newFieldIdFixed = re.sub(r' ', '', newFieldId)
							newHierarchy.addNewField(newFieldIdFixed)  # newHierarchy = ('', [RACK]) .... newHierarchy = ('', [RACK, SHELF])
							newField = column()
							newField.create(newFieldIdFixed, hierarchyName[position], validateUdn(newFieldIdFixed), validateSqlName(newFieldIdFixed), newFieldId, 'ID', 'VARCHAR2(256)', 'STRING', 'STRING', 'STRING', '')
							unitObj.addAttribute(newFieldIdFixed, newField)
							# newField.create(newFieldId, hierarchyName[position], validateUdn(newFieldId), validateSqlName(newFieldId), newFieldId, 'ID', 'VARCHAR2(255)', 'STRING', 'STRING', 'STRING', '')
							# unitObj.addAttribute(newFieldId, newField)

			# Generate pattern based on hierarchy fields to be generated
			# Example #usecase:
			# pattern = 'RACK=(?P<RACK>[^ ]+?)'
			# pattern = 'RACK=(?P<RACK>[^ ]+?),SHELF=(?P<SHELF>[^ ]+?)...'
			pattern = ''
			sep = ''
			for idx, attributeId in enumerate(newHierarchy.newFields):
				pattern += sep + saveIdForPattern[idx] + '=' + '(?P<' + attributeId.upper() + '>[^' + ' ' + ']+?)'
				sep = ','

			newHierarchy.pattern = pattern + '$'
			unitObj.addHierarchy(pattern, newHierarchy)

# interChar = ' '
# RACK=(?P<RACK>[^ ]+?),SHELF=(?P<SHELF>[^ ]+?),SLOT=(?P<SLOT>[^ ]+?),PORT=(?P<PORT>[^ ]+?),ONU=(?P<ONU>[^ ]+?),GPON ONU Ethernet Port=(?P<GPONONUEthernetPort>[^ ]+?)$