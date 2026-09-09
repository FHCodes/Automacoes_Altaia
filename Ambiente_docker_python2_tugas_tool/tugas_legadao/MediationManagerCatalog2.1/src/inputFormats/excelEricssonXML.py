__doc__ = \
	__version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

from lxml import etree;
from lib.objects.column import column
from lib.objects.table import table
from lib.objects.unit import unit
from lib.functions import validateInformation
import re
import json
from collections import OrderedDict
from src.inputFormats.hdxFormat import readHDXFile
from lib.Logger import Logger

# #
# Ericsson xml data processor
# #
def process(docPath, fileConfigName, dataConfig, vendor):
	logger = Logger('processLogger').get()
	catalogType = dataConfig['collector']['collectorType']

	# Insert Code Here

	relationships = getRelationship(docPath)
	if catalogType == 'PM':
		data = getPMData(logger, docPath, relationships)
		print data['BatteryUnit'].getTable('BatteryUnit').counters.keys()#.getCounter('pmBatteryCellVoltageMax')
		return data
	elif catalogType == 'CM':
		structs = getStrucs(docPath)
		return getDataCM(logger, docPath, relationships, structs)

def getPMData(logger, docPath, relationships):
	root = etree.parse(docPath)
	data = dict()
	createUnit = False

	for classElemet in root.xpath('//class'):
		classId = classElemet.attrib['name']
		try:
			description = classElemet.find('description').text
		except:
			description = ''

		createUnit = False
		unitObj = unit()
		unitObj.create(classId, classId, classId, description, buildHierarchy(classId, relationships))

		tableObj = table()
		tableObj.create(classId, classId, classId, classId)
		unitObj.addTable(classId, tableObj)

		for attribute in classElemet.findall('attribute'):
			counterType = attribute.find('counterType')
			if counterType != None:
				columnObj = getCounter(attribute)
				if columnObj.typeId in tableObj.counters.keys():
					logger.warning(
						' * Duplicated column id \"{:s}\" in table \"{:s}\", new information was discarted * '.format(
							columnObj.typeId, classId))
					continue

				if 'VARCHAR2(' in columnObj.bdtype or 'TIMESTAMP(' in columnObj.bdtype:
					columnObj.update('BDTYPE', 'ID')
				else:
					columnObj.update('BDTYPE', 'MT')

				if columnObj.dbn0type in ['PK', 'ID']:
					unitObj.addAttribute(columnObj.typeId, columnObj)
				else:
					tableObj.addCounter(columnObj.typeId, columnObj)
				createUnit = True

		if createUnit and classId not in data.keys():
			data[classId] = unitObj
	return data

def getPMDatav2(logger, docPath, relationships):
	context = iter(etree.iterparse(docPath, events=('start', 'end')))
	# get root element
	_, root = next(context)

	tag = ['class', 'description', 'attribute', 'dataType', 'counterType', 'unit']

	columnObj = None
	data = dict()
	addUnit = False
	addCounter = False
	dimension = None

	if isinstance(tag, list):
		multi = True
	else:
		multi = False

	namespace = None
	for event, elem in context:

		if event == 'start' and namespace is None:
			if "}" in elem.tag:
				namespace = elem.tag.split("}")[0].strip("{")
				namespace = "{" + namespace + "}"
			else:
				namespace = ""

		if multi:
			if event == 'start':
				if elem.tag == namespace + 'class':
					classId = elem.attrib['name']
					if classId in data.keys():
						unitObj = data[classId]
					else:
						unitObj = unit()
						unitObj.create(classId, classId, classId, '', buildHierarchy(classId, relationships))
					if classId in unitObj.tables.keys():
						tableObj = unitObj.getTable(classId)
					else:
						tableObj = table()
						tableObj.create(classId, classId, classId, classId)
						unitObj.addTable(classId, tableObj)

					#codigo a familia

					elem.clear()

				elif elem.tag == namespace + 'description':
					try:
						if elem.text != None:
							if columnObj != None:
								columnObj.update('DESC', re.sub(r'\n|\t|\r', ' ', elem.text))
							else:
								unitObj.update('DESC', re.sub(r'\n|\t|\r', ' ', elem.text))
					except:
						pass

					elem.clear()

				elif elem.tag == namespace + 'attribute':
					dimension = None
					columnObj = column()
					attrId = elem.attrib['name']
					columnObj.create(attrId, attrId, attrId, attrId, '', '', '', '', '', '', '')
					elem.clear()

				elif elem.tag == namespace + 'dataType':
					try:
						for e in elem:
							if columnObj.bdtype == '' and e.text not in [None, '']:
								columnObj.update('BDTYPE', re.sub(r'\n|\t|\r', ' ', elem.text).strip())
							break
					except:
						pass
					if columnObj != None:
						if columnObj.typeId == 'pmUeMeasRsrqDeltaIntraFreq1':
							print etree.tostring(elem)
							dimension = getDimension(elem)
							print dimension
					elem.clear()

				elif elem.tag == namespace + 'counterType':
					#insert code here
					addUnit = True
					addCounter = True
					try:
						if elem.text in [None, '']:
							print classId
							print etree.tostring(elem)
						elif elem.text not in [None, '']:
							columnObj.update('TYPEVENDOR', re.sub(r'\n|\t|\r', '', elem.text).strip())
							if columnObj.bdtype == '':
								columnObj.update('BDTYPE', re.sub(r'\n|\t|\r', '', elem.text).strip())
							if columnObj.typeCust in ['', None]:
								columnObj.update('TYPECUST', re.sub(r'\n|\t|\r', '', elem.text).strip())
					except:
						pass
					elem.clear()

				elif elem.tag == namespace + 'unit':
					try:
						if elem.text not in [None, '']:
							if columnObj.bdtype == '':
								columnObj.update('BDTYPE', re.sub(r'\n|\t|\r', '', elem.text))
							columnObj.update('UNITVENDOR', re.sub(r'\n|\t|\r', '', elem.text))
					except:
						pass
					elem.clear()

			elif event == 'end':
				if elem.tag == namespace + 'class':
					if addUnit and unitObj.typeId not in data.keys():
						data[unitObj.typeId] = unitObj
					unitObj = None
					tableObj = None
					addUnit = False

				elif elem.tag == namespace + 'attribute':
					if addCounter:
						if columnObj.typeId in tableObj.counters.keys():
							logger.warning(
								' * Duplicated column id \"{:s}\" in table \"{:s}\", new information was discarted * '.format(
									columnObj.typeId, classId))
							continue

						if 'VARCHAR2(' in columnObj.bdtype or 'TIMESTAMP(' in columnObj.bdtype:
							columnObj.update('DBN0TYPE', 'ID')
						else:
							columnObj.update('DBN0TYPE', 'MT')

						#if columnObj.typeCust not in ['PDF', 'DDM']:
						if 'PDF ranges' in columnObj.desc:
							columnObj.update('TYPECUST', 'PDF')
							#	columnObj.multiplicity = int(re.search(r'.*\[(\d+)\]*[^[\]].*', columnObj.desc).group(1)) + 1

						if columnObj.typeId == 'pmUeMeasRsrqDeltaIntraFreq1':
							print dimension
						if columnObj.typeCust in ['PDF', 'DDM']:# and columnObj.multiplicity in [0, '']:
							if dimension != None:
								columnObj.multiplicity = int(dimension)
							else:
								print '{0}: {1}'.format(tableObj.typeId, columnObj.typeId)

						if columnObj.dbn0type in ['PK', 'ID']:
							unitObj.addAttribute(columnObj.typeId, columnObj)
						else:
							tableObj.addCounter(columnObj.typeId, columnObj)
					addCounter = False
					columnObj = None

				elem.clear()
		else:
			elem.clear()
	del context
	return data

def getDimension(elem):
	for e in elem:
		try:
			if e.tag == 'maxLength':
				return e.text
			#ex = e.find('maxLength')
			#print etree.tostring(ex)
			#return ex.text
		except:
			pass
		try:
			value = getDimension(e)
			if value != None:
				return value
		except:
			pass
	return None

def getDataCM(logger, docPath, relationships, structs):

	pass

def getStrucs(path):
	root = etree.parse(path)
	structs = dict()
	for struct in root.xpath('//struct'):
		structId = struct.attrib['name']
		if structId not in structs.keys():
			structs[structId] = dict()
		for structMember in struct.findall('structMember'):
			structMemberId = structMember.attrib['name']
			if structMemberId not in structs[structId].keys():
				try:
					structs[structId][structMemberId] = structMember.find('description').text
				except:
					structs[structId][structMemberId] = ''
	return structs

def getRelationship(path):
	root = etree.parse(path)
	relationships = dict()

	for relationship in root.xpath('//relationship'):
		try:
			parent = relationship.find('containment').find('parent').find('hasClass').attrib['name']
			child = relationship.find('containment').find('child').find('hasClass').attrib['name']
			if child not in relationships.keys():
				relationships[child] = list()

			if parent not in relationships[child]:
				relationships[child].append(parent)
		except:
			pass
	return relationships

def getCounter(element):
	columnObj = column()
	columnObj.create(element.attrib['name'], element.attrib['name'], element.attrib['name'], element.attrib['name'],  '', '', '', '', '', '', '', '')
	data = {'description': ['DESC'], 'counterType': ['TYPEVENDOR', 'TYPECUST', 'BDTYPE']}
	for elementChild in element:
		try:
			for att in data[elementChild.tag]:
				columnObj.update(att, re.sub(r'\n|\t|\r', ' ', elementChild.text))
		except:
			unit = searchUnit(elementChild)
			if unit != None:
				columnObj.unitVendor = unit
			elif columnObj.unitVendor == '':
				try:
					columnObj.unitVendor = elementChild.find().tag
				except:
					pass
	if 'PDF ranges' in columnObj.desc:
		columnObj.update('TYPECUST', 'PDF')
		columnObj.multiplicity = int(re.search(r'.*\[(\d+)\]*[^[\]].*', columnObj.desc).group(1)) + 1

	if columnObj.typeCust in ['PDF', 'DDM']:  # and columnObj.multiplicity in [0, '']:
		dimension = getDimension(element.find('dataType'))
		if dimension != None:
			columnObj.multiplicity = int(dimension)

	return columnObj

def searchUnit(element):
	for child in element:
		if child.tag == 'unit':
			return child.text
		else:
			unit = searchUnit(child)
			if unit != None:
				return unit
	return None

def buildHierarchy(classId, relationships):
	hierarchy = ''
	sep = ''
	try:
		for child in relationships[classId]:
			hierarchy = '{0}{1}{2}-{3}'.format(hierarchy, sep, buildHierarchy(child, relationships), classId)
			sep = ','
		return hierarchy if hierarchy != '' else classId
	except:
		return classId