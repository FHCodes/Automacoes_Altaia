__doc__ = \
	__version__ = '1.1'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

import lxml.html as html
import xml.etree.ElementTree as ET
from lib.functions import *
import os

def copy_catalog_html(filepath):
	sampleTree = html.parse(filepath)
	root = sampleTree.getroot()
	return root

def validateTech(hierarchy, tech):
	if tech.upper() in ['ALL', '']:
		return False
	data = {'2G': ['BtsFunction', 'BscFunction', 'BscSupportFunction'], '3G': ['NodeSupport', 'NodeBFunction', 'RncFunction', 'TransportNetwork', 'EquipmentSupportFunction', 'IpSystem'], '4G': ['ENodeBFunction', 'EquipmentSupportFunction', 'IpSystem', 'IpOam'], '5G': ['GNBDUFunction', 'GNBCUUPFunction', 'IpSystem', 'GNBCUCPFunction']}
	acrossTech = {'SystemFunctions', 'Equipment', 'Transport'}
	try:
		value = (hierarchy.split('-'))[1]
		if value not in data[tech] and value not in acrossTech:
			return True
	except:
		return False
	return False

def fileProcess(fileName):
	file = open(fileName, 'r')
	lines = file.readlines()
	file.close()

	file = open(fileName, 'w')

	for line in lines:
		if 'xmlns' in line:
			line = line.replace('xmlns', 'xx')
		try:
			line = line.replace('&amp;', '&')
			line = line.replace('&#10', '')
			line = line.replace('&quot;', '')
			line = line.replace('&nbsp;', '')
			line = line.replace('&copy;', '')
			line = line.replace('&reg;', '')
			line = line.replace('class&#160;', '')
			line = line.replace('struct&#160;', '')
			line = line.replace('&bull;', '')
			line = line.replace('&#160;', '')
			if '<meta' in line and not ('/>' in line):
				line = line.replace('>', '/>')
		except:
			pass
		file.write(line)
	file.close()

def processData(root, measurementSheet, counterSheet, objectSheet, attributeSheet, pmGroupSheet, measurementTypeSheet, positions, path, tech):
	state = False
	try:
		head = root.find('head').find('title')
		# print head.text
		if 'CLASS' in head.text.split(' ')[0].upper():
			# Class
			try:
				positions = getClass(root.find('body'), measurementSheet, counterSheet, objectSheet, attributeSheet, pmGroupSheet, measurementTypeSheet, positions, path, tech)
			except Exception as ex:
				pass
		elif 'STRUCT' in head.text.split(' ')[0].upper():
			# Structure
			positions = getStruct(root.find('body'), measurementSheet, counterSheet, objectSheet,  attributeSheet, pmGroupSheet, measurementTypeSheet, positions, path, tech)
			pass
		elif 'MIB' in head.text.split(' ')[0].upper():
			# Structure
			try:
				positions = getInstance(root.find('body'), measurementSheet, counterSheet, objectSheet, attributeSheet, pmGroupSheet, measurementTypeSheet, positions, path)
			except Exception as e:
				print e
			pass
		elif 'ENUM' in head.text.split(' ')[0].upper():
			state = True
	except Exception as ex:
		# print ET.tostring(root)
		print ex
		print '[Error] While reading file'
	# processData(copy_catalog_html(file),measurementSheet,counterSheet,objectSheet,attributeSheet,positions,path,file)

	return (positions, state)

# #
# Gets the data of the struct (for parameters only)
# #
def getStruct(root, measurementSheet, counterSheet, objectSheet, attributeSheet, pmGroupSheet, measurementTypeSheet, positions, path, tech):

	families = []
	tmp = []
	fathers = []
	sons = []
	(m, c, o, p, pg, mt) = positions
	try:
		# pprint.pprint(ET.tostring(root))
		for name in root.findall('h1'):
			getA = name.find('a')
			familyP = ''
			if getA != None:
				familyP = getA.text.replace('struct','').strip()
			else:
				familyP = name.text.replace('struct','').strip()
			# hierarchy = gethierarchy(root,family,path,True)
			hierarchy = ''
			table = root.find('table')
			root.remove(table)
			try:
				# print ET.tostring(table)
				descriptionP = re.sub(r'[^\x01-\x7F]', '', getText(getElement(table, 'p')))
			except:
				try:
					table = root.find('table')
					descriptionP = re.sub(r'[^\x01-\x7F]', '', getText(getElement(table, 'p')))
					root.remove(table)
				except Exception as ex:
					print ex
					description = ''
			# if 'ALARM' in description.upper():
			#	print 'Struct '+ family +' - '+ description +'\n'
			tmp.append((familyP, hierarchy, descriptionP))

			# print family
			if validateTech(hierarchy, tech):
				return (m, c, o, p, pg, mt)
	except Exception as ex:
		print ex

	try:
		if tmp != []:
			test = root.find('dl')
			fathers, sons = getFathers(test)
	except:
		print 'erro a buscar pais nas structs'
		return (m, c, o, p, pg, mt)

	if fathers == []:
		return (m, c, o, p, pg, mt)

	# print ET.tostring(root.find('table'))
	attributes = getAttributes(root.find('table'))
	#for (family, hierarchy, description) in tmp:
	#	for father in fathers:
	#		for (counterName, counterType, desc) in attributes:
	#			attributeSheet = writeToSheet(attributeSheet, [father + '_' + family, counterName, counterType.replace('&#160;', ''), desc], p, False)
	#			p += 1
	#		objectSheet = writeToSheet(objectSheet, [father, family, father + '_' + family, hierarchy, description, 'False'], o, False)
	#		o += 1

	for (counterName, counterType, desc) in attributes:
		attributeSheet = writeToSheet(attributeSheet, [familyP, counterName, counterType.replace('&#160;', ''), desc, 'True', ''], p, False)
		p += 1
	objectSheet = writeToSheet(objectSheet, [familyP, familyP, familyP, '', descriptionP, 'True', ''], o, False)
	o += 1

	return (m, c, o, p, pg, mt)

# #
# Gets the data of the class
# #
def getClass(root, measurementSheet, counterSheet, objectSheet, attributeSheet, pmGroupSheet, measurementTypeSheet, positions, path, tech):

	families = []
	tmp = []
	# header = 'Name;hierarchy;Description\n'
	(m, c, o, p, pg, mt) = positions

	for name in root.findall('h1'):
		family = name.find('a').text.split('class')[1].strip()

		hierarchy = gethierarchy(root, family, path, list())
		table = root.find('table')
		try:
			# print ET.tostring(table)
			description = re.sub(r'[^\x01-\x7F]', '', getText(getElement(table, 'p')))
			root.remove(table)
		except:
			try:
				table = root.find('table')
				description = re.sub(r'[^\x01-\x7F]', '', getText(getElement(table, 'p')))
				root.remove(table)
			except:
				description = ''
		# if 'ALARM' in description.upper():
		#	print 'Class '+ family +' - '+ description +'\n'
		tmp.append((family, hierarchy, description))

	# print family
	if validateTech(hierarchy, tech):
		return (m, c, o, p, pg, mt)
	try:
		for field in root.findall('table'):
			# print '1'
			try:
				# print field.find('tr').find('td').find('b').text
				if 'PM COUNTERS' == field.find('tr').find('td').find('b').text.upper():
					# print '3'
					attributes = getAttributes(field)
					for (family, hierarchy, description) in tmp:
						flag = False
						for (counterName, size, desc) in attributes:
							try:
								if 'Counter type:  ' in desc:
									counterType = ((desc.split('Counter type:  ')[1]).split(' ')[0]).replace('&#160;', '')
								elif 'Counter type: ' in desc:
									counterType = ((desc.split('Counter type: ')[1]).split(' ')[0]).replace('&#160;', '')
								else:
									counterType = ((desc.split('Counter type:')[1]).split(' ')[0]).replace('&#160;', '')
							except:
								counterType = ''
							counterSheet = writeToSheet(counterSheet, [family, counterName, counterType, counterType, getSize(size), desc], c, False)
							flag = True
							c += 1
						if flag:
							# Adicionar familia
							measurementSheet = writeToSheet(measurementSheet, [family, hierarchy, description], m, False)
							m += 1
				elif 'ATTRIBUTES' == field.find('tr').find('td').find('b').text.upper():
					# print '4'
					attributes = getAttributes(field)
					for (family, hierarchy, description) in tmp:
						flag = False
						for (counterName, counterType, desc) in attributes:
							counterType = counterType.replace('&#160;', '')
							attributeSheet = writeToSheet(attributeSheet, [family, counterName, counterType, desc, 'False', hierarchy], p, False)
							p += 1
							flag = True

						if flag:
							# Adicionar familia
							objectSheet = writeToSheet(objectSheet, [family, family, family, hierarchy, description, 'False', hierarchy], o, False)
							o += 1
			except Exception as ex:
				print ex
	except Exception as e:
		print '[Error 10] While creating family'
		pass

	return (m, c, o, p, pg, mt)

# #
# Gets the data from the instances
# #
def getInstance(root, measurementSheet, counterSheet, objectSheet, attributeSheet, pmGroupSheet, measurementTypeSheet, positions, path):

	(m, c, o, p, pg, mt) = positions

	dataType = None
	unitDocument = {"category": "","consistentData": "","generation": "","moClass.moClassName": "","moClass.mimName": "","moClass.mimVersion": "","moClass.mimRelease": "","pmGroupId": "","pmGroupVersion": "","switchingTechnology": "","validity": ""}
	counterDocument = {"aggregation":"","collectionMethod":"","condition":"","cpiHeading":"","description":"","measurementName":"","measurementResult":"","measurementStatus":"","measurementTypeId":"","multiplicity":"","size":""}

	for elem in root:
		if elem.tag == 'a':
			if elem.text == 'PmGroup':
				dataType = 'PmGroup'
				unitDocument = {"category": "","consistentData": "","generation": "","moClass.moClassName": "","moClass.mimName": "","moClass.mimVersion": "","moClass.mimRelease": "","pmGroupId": "","pmGroupVersion": "","switchingTechnology": "","validity": ""}
			elif elem.text == 'MeasurementType':
				dataType = 'MeasurementType'
				counterDocument = {"aggregation":"","collectionMethod":"","condition":"","cpiHeading":"","description":"","measurementName":"","measurementResult":"","measurementStatus":"","measurementTypeId":"","multiplicity":"","size":""}
		elif elem.tag == 'table':
			if dataType == 'PmGroup':
				body = elem.find('tbody')
				for info in body:
					fieldName = ""
					fieldValue = ""
					for td in info.findall('td'):
						if fieldName == "":
							fieldName = td.text
						elif fieldValue == "":
							fieldValue = td.text
					unitDocument[fieldName] = fieldValue
				pmGroupSheet = writeToSheet(pmGroupSheet,[unitDocument["category"],unitDocument["consistentData"],unitDocument["generation"],unitDocument["moClass.moClassName"],unitDocument["moClass.mimName"],unitDocument["moClass.mimVersion"],unitDocument["moClass.mimRelease"],unitDocument["pmGroupId"],unitDocument["pmGroupVersion"],unitDocument["switchingTechnology"],unitDocument["validity"]], pg, False)
				pg += 1
			elif dataType == 'MeasurementType':
				body = elem.find('tbody')
				for info in body.findall('tr'):
					fieldName = ""
					fieldValue = ""
					for td in info.findall('td'):
						if fieldName == "":
							fieldName = td.text
						elif fieldValue == "":
							fieldValue = td.text
					counterDocument[fieldName] = fieldValue
				counterList = [counterDocument["aggregation"], counterDocument["collectionMethod"], counterDocument["condition"],counterDocument["cpiHeading"], counterDocument["description"], counterDocument["measurementName"],counterDocument["measurementResult"], counterDocument["measurementStatus"],counterDocument["measurementTypeId"], counterDocument["multiplicity"], counterDocument["size"]]
				for key in counterDocument.keys():
					if key not in ["aggregation","collectionMethod","condition","cpiHeading","description","measurementName","measurementResult","measurementStatus","measurementTypeId","multiplicity","size"]:
						counterList.append('{0}: {1}'.format(key, counterDocument[key]))
				measurementTypeSheet = writeToSheet(measurementTypeSheet, counterList, mt, False)
				mt += 1

	return (m, c, o, p, pg, mt)

def getAttributes(root):

	data = []
	# print len(root.findall('tr'))
	if root != None:
		for tr in root.findall('tr'):
			if tr.get('valign') != None:
				counterType = ''
				counterName = ''
				description = ''

				for td in tr.findall('td'):
					tmp = getElement(td, 'a')
					if tmp == None:
						tmp = getElement(td, 'code')

					if tmp.get('name') == None:
						if tmp == None:
							# print tmp
							counterType = getText(getElement(td, 'code')).split(' ')[0]
						else:
							counterType = tmp.text
					else:
						if tmp == None:
							counterName = getText(getElement(td, 'code')).split(' ')[0]
						else:
							counterName = tmp.text

				description = getText(getElement(tr, 'dd'))
				# print counterName
				description = re.sub(r'[^\x01-\x7F]', '', description)
				data.append((counterName, counterType, description))
	return data

def getFathers(root):
	fathers = []
	sons = []
	for element in root.findall('dt'):
		if element.find('b').text.upper() == 'REFERENCES TO:':
			root.remove(root.find('dd'))
		# Creates sons
		elif element.find('b').text.upper() == 'REFERENCES FROM:':
			for a in root.find('dd').findall('a'):
				fathers.append(a.text)
			pass
	# Gets fathers names
	return (fathers, sons)

def gethierarchy(root, family, path, backTrack):
	data = ''
	sep = ''
	flag = True
	backTrack.append(family.upper())
	dlList = root.findall('dl')

	while flag:

		hierarchy = ''
		dl = root.find('dl')
		if dl == None:
			flag = False
			continue

		if dl.find('dt') != None:
			flag = False
			continue

		dd = dl.find('dd')
		if dd == None:
			flag = False
			continue

		file = ''

		##PEGAR HIERARQUIA FILHA
		if dd.text == '..':

			dl.remove(dd)
			dd = dl.find('dd')

			innerRoot = copy_catalog_html(path + getElement(dd, 'a').get('href').replace('edw:/alex?fn=', ''))
			innerFamily = getElement(innerRoot, 'h1').find('a').text.split('class')[1].strip()

			if innerFamily.upper() in backTrack:
				continue
			else:
				tt = gethierarchy(innerRoot.find('body'), innerFamily, path, backTrack)
				if tt == '':
					print path + getElement(dd, 'a').get('href').replace('edw:/alex?fn=', '')
				temp = tt.split(', ')

			afterHierar = getHierarField(dd, backTrack)
			if afterHierar != '':
				afterHierar += '-'
			afterHierar += family

			tSep = ''
			for t in temp:
				if t != '' and not t.startswith('-'):
					hierarchy += tSep + t + '-' + afterHierar
					tSep = ', '

			data += sep + hierarchy
			sep = ', '

		else:
			t = getHierarField(dl, backTrack)
			if t != '':
				data += sep + t + '-' + family
			else:
				data += sep + family
			sep = ', '
		root.remove(dl)

	tmp = ''
	sep = ''
	for d in data.split(', '):
		if d not in tmp:
			tmp += sep + d
			sep = ', '
	return tmp

def getHierarField(root, backTrack):
	dd = getElement(root, 'dd')
	if dd == None:
		return ''

	a = getElement(dd, 'a').text
	if a.upper() in backTrack:
		return ''

	nextField = getHierarField(dd, backTrack)
	if nextField != '':
		return a + '-' + nextField

	return a

def writeFamilyToCSV(fileName, header, data):
	if os.path.isfile(fileName):
		file = open(fileName, 'a')
	else:
		file = open(fileName, 'w')
		file.write(header)
	file.write(data)
	file.close()

def getElement(root, tag):
	try:
		for element in root:
			if element.tag == tag:
				return element
			else:
				elem = getElement(element, tag)
				if elem != None:
					return elem
	except:
		pass
	return None

def getElementList(root, tag):
	elements = []
	for element in root:
		if element.tag == tag:
			elements.append(element)
			tmp = []
			try:
				tmp = getElementList(element, tag)
			except:
				pass
			if tmp != []:
				for i in tmp:
					elements.append(i)
		else:
			elem = []
			try:
				elem = getElementList(element, tag)
			except:
				pass
			if elem != []:
				for i in elem:
					elements.append(i)
	return elements

def getText(root):
	text = ET.tostring(root)
	data = ''

	try:
		t = text.split('>')
		for i in range(1, len(t) - 1):
			tmp = t[i].split('<')[0]
			if tmp != '':
				data += tmp + ' '
	except:
		print "ERROR READING"

	data = data.replace('&amp;', '&')
	data = data.replace('&#10', '')
	data = data.replace('&quot;', '')
	data = data.replace('&nbsp;', '')
	data = data.replace('&copy;', '')
	data = data.replace('&reg;', '')
	data = data.replace('class&#160;', '')
	data = data.replace('struct&#160;', '')
	data = data.replace('&bull;', '')
	data = data.replace('&#160;', '')

	return data

def getSize(data):
	
	if '..' in data:
		return (data.split('..')[1]).split(']')[0]
	if '[' in data:
		return (data.split('[')[1]).split(']')[0]
	return ''

# #
# Gets the ALX version
# #
def getAlxName(path):
	fileName = 'notFound'
	file = path + 'elexmain.html'
	fileProcess(file)
	root = copy_catalog_html(file).find('head')
	for meta in root.findall('meta'):
		if meta.get('name') == 'REF':
			return meta.get('content')
	return fileName

def readAlexFile(path):
	fileName = getAlxName(path)
	if os.path.isfile('./output/' + fileName + '.xls'):
		answer = raw_input('File ' + fileName + ' already exists, overwrite (Y/N): ')
		if 'Y' in answer.upper():
			print '-> Start processing alx data to Excel....'
			os.remove('./output/' + fileName + '.xls')
			transform(fileName, path)
			print '-> Finish processing alx.'
			return './output/' + fileName + '.xls'
		elif 'N' in answer.upper():
			return './output/' + fileName + '.xls'
	else:
		print '-> Start processing alx data to Excel....'
		transform(fileName, path)
		print '-> Finish processing alx.'
	return './output/' + fileName + '.xls'

def transform(fileName, path):

	fileList = [path + f for f in os.listdir(path) if os.path.isfile(path + f)]
	workbook = createExcel()

	measurementSheet = createSheet(workbook, 'Measurement List')
	writeToSheet(measurementSheet, ['Name', 'Hierarchy', 'Description'], 0, True)
	counterSheet = createSheet(workbook, 'Counter List')
	writeToSheet(counterSheet, ['MO', 'Name', 'Type', 'Unit', 'Size', 'Description'], 0, True)

	objectSheet = createSheet(workbook, 'Object List')
	writeToSheet(objectSheet, ['OssId', 'Origin', 'Name', 'Hierarchy', 'Description', 'isStruct'], 0, True)
	attributeSheet = createSheet(workbook, 'Parameter List')
	writeToSheet(attributeSheet, ['MO', 'Name', 'Type', 'Description', 'isStruct', 'Hierarchy'], 0, True)

	pmGroupSheet = createSheet(workbook, 'PmGroup')
	writeToSheet(pmGroupSheet, ['category', 'consistentData', 'generation', 'moClass.moClassName', 'moClass.mimName', 'moClass.mimVersion', 'moClass.mimRelease', 'pmGroupId', 'pmGroupVersion', 'switchingTechnology', 'validity'], 0, True)
	measurementTypeSheet = createSheet(workbook, 'MeasurementType')
	writeToSheet(measurementTypeSheet, ['aggregation', 'collectionMethod', 'condition', 'cpiHeading', 'description', 'measurementName', 'measurementResult', 'measurementStatus', 'measurementTypeId', 'multiplicity', 'size'], 0, True)

	positions = (1, 1, 1, 1, 1, 1)

	inputName = raw_input('Nomenclature of file: ')
	tech = raw_input('Technology of data: ')

	for file in fileList:
		if inputName in file:
			# fileProcess(file)
			# print file
			root = copy_catalog_html(file)
			positions, state = processData(root, measurementSheet, counterSheet, objectSheet, attributeSheet, pmGroupSheet, measurementTypeSheet, positions, path, tech)
			if state:
				os.remove(file)
		elif not ('.html' in file):
			print '[REMOVED]: ' + file
			os.remove(file)
			pass

	writeToExcel(fileName, workbook)
