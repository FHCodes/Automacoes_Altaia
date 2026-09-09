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

def process(unitDict, config):

	if 'format' not in config.keys():
		config['format'] = 'XML'

	hf = None
	regexList = list()
	genericMeasObj = ''
	sep = ''
	genericUnit = unit.unit()
	unitObj = None
	for ossId in unitDict.keys():
		unitObj = unitDict[ossId]
		genericUnit.addHierarchies(unitObj.hierarchyList)
		genericUnit.addAttributes(unitObj.attributes)
		unitObj.disableHierarchy()
		try:
			genericUnit.addOperations('unit', unitObj.getOperations('unit'))
		except:
			pass
		try:
			genericUnit.addOperations('item', unitObj.getOperations('item'))
		except:
			pass

		for measObjBase in unitObj.measuredObject.split(config['interChar']):
			measObjBase = measObjBase.replace(' ', '')
			#measObjBase = 'SubNetwork,ManagedElement,'+measObjBase
			if measObjBase not in regexList:
				if len(regexList) == 1:
					sep = config['interChar']
				regexList.append(measObjBase)
				genericMeasObj = '{:s}{:s}{:s}'.format(genericMeasObj, sep, measObjBase)

			for dataBlock in measObjBase.split(config['sepCharDoc']):
				fields = list(dataBlock.split(config["sepCharPattern"]))

				try:
					myValue = fields[1]
				except:
					myValue = ''
				if hf != None:
					hf = hf.addNode(fields[0], myValue, '')
					print 'new'
				else:
					print 'update'
					hf = hierarchyField(fields[0], hf, myValue, '')
			hf.addFamId(ossId)
			hf = hf.goToFirst()
	#hf.printData()

	genericUnit.measuredObject = genericMeasObj

	genericUnit.activeHierarchy()
	print '1'
	unitSplitList = hf.getDeps(hf, dict(), config)
	print '2'
	#print unitSplitList

	genericUnit.create('GENERIC', 'GENERIC', 'GENERIC', 'Dummy generic family', genericMeasObj)
	unitDict['GENERIC'] = genericUnit
	genericTable = table.table()
	genericTable.create('GENERIC', 'GENERIC', 'GENERIC_DUMMY', 'GENERIC_DUMMY')
	genericTable.setDummy()
	measItem = column.column()
	measItem.create('measObjLdn'.upper(),'measObjLdn','measObjLdn','measObjLdn','measObjLdn','PK','VARCHAR2(255)','STRING','STRING','STRING','','')
	genericUnit.addAttribute('measObjLdn'.upper(), measItem)
	print 'tech'
	print unitObj.tech
	genericTable.tech = unitObj.tech
	genericUnit.addTable('GENERIC', genericTable)

	matchList = dict()

	for pattern in unitSplitList.keys():
		matchList = dict()
		newUnitName = '{:s}{:s}{:s}'.format(unitSplitList[pattern]['level'], '' if unitSplitList[pattern]['value'] == '' else '_', unitSplitList[pattern]['value']).upper()
		info = dict()
		info['field'] = unitSplitList[pattern]['level'].upper()
		info['pattern'] = pattern
		info['newUnit'] = newUnitName
		addOpe = False

		if config['format'] == 'json':
			op = OrderedDict()
			try:
				opU = genericUnit.getOperation('unit', 'unitSplitv2')
			except:
				opU = None

			if opU == None:
				opU = list()
				opU.append(op)
				addOpe = True
				op['type'] = 'unitSplit'
				op['def'] = list()

			flagged = False
			for op in opU:
				if len(op['def']) > 0:
					fieldFound = False
					for itDef in op['def']:
						if itDef['id'] == 'MEASOBJLDN':
							fieldFound = True
							regexFound = False
							patternFound = False
							for regexInfo in itDef['regexes']:
								if regexInfo['newUnit'] == info['newUnit'].upper():
									regexFound = True
									if regexInfo['pattern'] == info['pattern']:
										patternFound = True
										break
							if not regexFound or not patternFound:
								regexItem = OrderedDict()
								regexItem['newUnit'] = info['newUnit'].upper()
								regexItem['pattern'] = info['pattern']
								itDef['regexes'].append(regexItem)
							break
					flagged = True
					break
			if not flagged:
				itDef = OrderedDict()
				itDef['id'] = 'MEASOBJLDN'
				itDef['regexes'] = list()
				regexItem = OrderedDict()
				regexItem['newUnit'] = info['newUnit'].upper()
				regexItem['pattern'] = info['pattern']
				itDef['regexes'].append(regexItem)
				op['def'].append(itDef)

		else:
			field = None
			try:
				op = genericUnit.getOperation('unit', 'unitSplitv2')
				for opInfo in op:
					#print ET.tostring(opInfo)
					idField = opInfo.find('field')
					#print ET.tostring(idField)
					#print idField.attrib.keys()
					if idField.attrib['id'] == 'MEASOBJLDN':
						field = idField
						op = opInfo
				if op == genericUnit.getOperation('unit', 'unitSplitv2'):
					op = None
			except Exception as ex:
				print ex
				op = None

			if op == None:
				addOpe = True
				op = ET.Element('operation')
				op.set('type', 'unitSplit')
				field = ET.SubElement(op, 'field')
				field.set('id', 'MEASOBJLDN')

			if field == None:
				field = ET.SubElement(op, 'field')
				field.set('id', info['field'])

			regex = ET.SubElement(field, 'regex')
			regex.set('pattern', info['pattern'])
			regex.set('newunit', info['newUnit'])

		if addOpe:
			genericUnit.addOperation('unit', 'unitSplitv2', op)

		newUnit = unit.unit()
		newUnit.create(newUnitName, newUnitName, newUnitName, 'Dummy_{:s}'.format(newUnitName), '')
		newUnit.disableHierarchy()

		#implementacao de operacao measurementPartitioner
		for pos, primaryFamily in enumerate(unitSplitList[pattern]['familyList'][:-1]):
			primaryFamilyObj = unitDict[primaryFamily]
			primaryList = [x.upper() for x in primaryFamilyObj.attributes.keys()]
			for pTableId in primaryFamilyObj.tables.keys():
				primaryList = primaryList + [x.upper() for x in primaryFamilyObj.getTable(pTableId).counters.keys()]
			for secundaryFamily in unitSplitList[pattern]['familyList'][pos+1:]:
				secundaryFamilyObj = unitDict[secundaryFamily]
				secundaryList = [x.upper() for x in secundaryFamilyObj.attributes.keys()]
				for stableId in secundaryFamilyObj.tables.keys():
					secundaryList = secundaryList + [x.upper() for x in secundaryFamilyObj.getTable(stableId).counters.keys()]

				matchPk = '-'
				matchPk = matchPk.join(set(primaryList) & set(secundaryList))
				if matchPk not in matchList .keys():
					matchList[matchPk] = dict()
					matchList[matchPk]['units'] = list()
					matchList[matchPk]['sharedFields'] = list(set(primaryList) & set(secundaryList))
					matchList[matchPk]['level'] = len(matchList[matchPk]['sharedFields'])
					matchList[matchPk]['priority'] = len(list(set([x.upper() for x in primaryFamilyObj.getTable(pTableId).counters.keys()]) & set([x.upper() for x in secundaryFamilyObj.getTable(stableId).counters.keys()])))
					if primaryFamily.upper() not in matchList[matchPk]['units']:
						matchList[matchPk]['units'].append(primaryFamily.upper())
				if secundaryFamily.upper() not in matchList[matchPk]['units']:
					matchList[matchPk]['units'].append(secundaryFamily.upper())
		if matchList.keys() == []:
			matchPk = '-'
			primaryFamily = unitSplitList[pattern]['familyList'][0]
			primaryFamilyObj = unitDict[primaryFamily]
			matchPk = matchPk.join(primaryFamilyObj.attributes.keys())
			matchList[matchPk] = dict()
			matchList[matchPk]['units'] = list()
			matchList[matchPk]['level'] = len(primaryFamilyObj.attributes.keys())
			matchList[matchPk]['priority'] = 0
			matchList[matchPk]['units'].append(primaryFamily.upper())
			matchList[matchPk]['sharedFields'] = [x.upper() for x in primaryFamilyObj.attributes.keys()]

		#if newUnitName.upper() == 'POOLTYPE_PAPS':
		#	print matchList
		newUnit.addOperation('unit', 'measurementParticioner', matchList)
		unitDict[newUnitName] = newUnit

		newTable = table.table()
		newTable.create(newUnitName, newUnitName, '{:s}{:s}'.format(newUnitName, '_DUMMY'), '{:s}{:s}'.format(newUnitName, '_DUMMY'))
		newTable.tech = unitObj.tech
		newTable.setDummy()
		newUnit.addTable(newUnitName, newTable)
	structMeasurementParticioner(unitDict)
	return unitDict


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