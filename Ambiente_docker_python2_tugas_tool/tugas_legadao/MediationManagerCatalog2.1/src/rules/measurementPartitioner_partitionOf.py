__doc__ = \
	__version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

###
# regex -> applies a sub regex to remove info from measuredObject
# sepCharDoc -> designed char for separate the hierarchy fields
# sepCharPattern -> char used in samples
# interChar -> chars tha cant be contained in find
# startText -> TBD
###

import re
from lib.objects.hierarchyField import hierarchyField
from lib.objects import unit
from lib.objects import table
from lib.objects import column
from lib.functions import *
from collections import OrderedDict
from collections import Counter

def process(unitDict, config):

	if 'format' not in config.keys():
		config['format'] = 'XML'
	elif config['format'].upper() == 'XML':
		config['format'] = 'XML'

	partitionerMapping = dict()

	unitList = unitDict.keys()
	for unitId in unitList:
		unitObj = unitDict[unitId]
		tableList = unitObj.tables.keys()
		for tableId in tableList:
			tableObj = unitObj.getTable(tableId)
			if tableObj.partitionOf != '':
				if tableObj.partitionOf.upper() != tableObj.typeId.upper():
					#its to apply the measurementPartition
					if tableObj.partitionOf not in unitDict.keys():
						genericUnit = unit.unit()
						genericUnit.create(tableObj.partitionOf, tableObj.partitionOf, tableObj.partitionOf, 'Dummy {:s} family'.format(tableObj.partitionOf), '')
						genericUnit.addAttributes(tableObj.getAttributes())
						unitDict[tableObj.partitionOf] = genericUnit
					elif tableObj.partitionOf not in unitDict[tableObj.partitionOf].tables.keys():
						genericUnit = unitDict[tableObj.partitionOf]
						genericTable = table.table()
						genericTable.create(tableObj.partitionOf, tableObj.partitionOf, tableObj.partitionOf, tableObj.partitionOf)
						genericTable.setDummy()
						genericUnit.update('TECH', unitObj.tech)
						genericUnit.update('DESC', 'Dummy {:s} family'.format(tableObj.partitionOf))
						genericTable.tech = unitObj.tech
						genericUnit.addTable(tableObj.partitionOf, genericTable)

				if tableObj.partitionOf not in partitionerMapping.keys():
					partitionerMapping[tableObj.partitionOf] = dict()
					partitionerMapping[tableObj.partitionOf][tableObj.partitionOf] = list()

				partitionerMapping[tableObj.partitionOf][tableId] = tableObj.counters.keys()

	#print partitionerMapping
	for unitId in partitionerMapping.keys():
		unitObj = unitDict[unitId]
		if len(partitionerMapping[unitId].keys()) == 1:
			continue
		mapByUnit = dict()
		tableList = partitionerMapping[unitId].keys()
		i = 1
		for fTableId in tableList[:-1]:
			for sTableId in tableList[i:]:
				compareResult = sorted(list(set(partitionerMapping[unitId][fTableId]) & set(partitionerMapping[unitId][sTableId])))
				if compareResult != []:
					compareResultStr = '-'.join([str(elem) for elem in compareResult])
				else:
					compareResultStr = ''

				if compareResultStr not in mapByUnit.keys():
					mapByUnit[compareResultStr] = dict()
					mapByUnit[compareResultStr]['tables'] = list()
					mapByUnit[compareResultStr]['counters'] = compareResult

				if fTableId not in mapByUnit[compareResultStr]['tables'] and fTableId != unitId:
					mapByUnit[compareResultStr]['tables'].append(fTableId)
				if sTableId not in mapByUnit[compareResultStr]['tables'] and sTableId != unitId:
					mapByUnit[compareResultStr]['tables'].append(sTableId)
			i += 1

		primaryFamilyObj = unitDict[unitId]
		primaryList = [x.upper() for x in primaryFamilyObj.attributes.keys()]
		for pTableId in partitionerMapping.keys():
			primaryList = list(set(primaryList) & set([x.upper() for x in unitDict[pTableId].attributes.keys()]))

		matchList = dict()
		info = getDecreasingList(mapByUnit)
		for pos in reversed(info.keys()):
			for key in info[pos]:
				matchInfo = mapByUnit[key]
				matchPk = '-'.join(set(primaryList) & set(matchInfo['counters']))
				if matchPk not in matchList.keys():
					matchList[matchPk] = dict()
					matchList[matchPk]['measurements'] = [x.upper() for x in matchInfo['tables']]
					matchList[matchPk]['sharedFields'] = primaryList + matchInfo['counters']

		#if matchList.keys() == []:
		#	matchPk = '-'
		#	primaryFamily = unitSplitList[pattern]['familyList'][0]
		#	primaryFamilyObj = unitDict[primaryFamily]
		#	matchPk = matchPk.join(primaryFamilyObj.attributes.keys())
		#	matchList[matchPk] = dict()
		#	matchList[matchPk]['units'] = list()
		#	matchList[matchPk]['level'] = len(primaryFamilyObj.attributes.keys())
		#	matchList[matchPk]['priority'] = 0
		#	matchList[matchPk]['units'].append(primaryFamily.upper())
		#	matchList[matchPk]['sharedFields'] = [x.upper() for x in primaryFamilyObj.attributes.keys()]

		unitObj.addOperation('unit', 'measurementParticioner', { 'type': "measurementPartition", 'def': [matchList[x] for x in matchList.keys()]})
		unitDict[unitId] = unitObj
	return unitDict


def getDecreasingList(dataMapping):
	endList = dict()
	for key in dataMapping.keys():
		try:
			dimension = (dict(Counter(key)))['-']
		except:
			dimension = 0

		if dimension not in endList.keys():
			endList[dimension] = list()
		endList[dimension].append(key)

	return endList


def structMeasurementParticioner(unitDict):
	for ossId in unitDict.keys():
		unitObj = unitDict[ossId]
		struct = dict()
		try:
			for oper in unitObj.getOperation('unit', 'measurementParticioner'):
				for operKey in oper.keys():
					priority = oper[operKey]['priority']
					if oper[operKey]['priority'] not in struct:
						struct[priority] = dict()
					level = oper[operKey]['level']
					if level not in struct[priority].keys():
						struct[priority][level] = list()

					data = dict()
					data['measurements'] = oper[operKey]['units']
					data['sharedFields'] = oper[operKey]['sharedFields']
					struct[priority][level].append(data)

			unitObj.removeOperation('unit', 'measurementParticioner')

			operDict = OrderedDict()
			operDict['type'] = 'measurementPartition'
			operDict['def'] = list()

			priorities = struct.keys()
			for priority in reversed(sorted(priorities)):
				values = struct[priority].keys()
				for level in reversed(sorted(values)):
					for item in struct[priority][level]:
						#print item
						op = OrderedDict()
						op['measurements'] = item['measurements']
						op['sharedFields'] = item['sharedFields']
						operDict['def'].append(op)
			unitObj.addOperation('unit', 'measurementPartition', operDict)
		except Exception as e:
			#print ossId
			#print e
			pass

	return unitDict