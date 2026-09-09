__doc__ = \
	__version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

from xml.etree.ElementTree import Element
import xml.etree.ElementTree as ET
import myTreeBuilder
import os
import xlwt
from xml.dom import minidom
import json
import re
from xml.sax.saxutils import unescape

def createExcel():
	return xlwt.Workbook()

def createSheet(workbook, sheetName):
	return workbook.add_sheet(sheetName)

def writeToSheet(sheet, data, row, bold):
	#config = xlwt.easyxf('font: bold ' + ('1' if bold else '0'))

	column = 0
	for info in data:
		sheet.write(row, column, info)#, config)
		column += 1

	return sheet

def writeToExcel(fileName, workbook):
	if not os.path.exists('output'):
		os.makedirs('output')

	workbook.save('./output/' + fileName + '.xls')

def reservedName(name, pfchar):
	reserved = ["USER", "ACCESS", "ADD", "ALL", "ALTER", "AND", "ANY", "AS", "ASC", "AUDIT", "BETWEEN", "BY",
				"CHAR", "CHECK", "CLUSTER", "COLUMN", "COMMENT", "COMPRESS", "CONNECT", "CREATE", "CURRENT", "DATE",
				"DECIMAL", "DEFAULT", "DELETE", "DESC", "DISTINCT", "DROP", "ELSE", "EXCLUSIVE", "EXISTS", "FILE",
				"FINALIZE", "FLOAT", "FOR", "FROM", "GRANT", "GROUP", "HAVING", "IDENTIFIED", "IMMEDIATE", "IN",
				"INCREMENT", "INDEX", "INITIAL", "INSERT", "INTEGER", "INTERSECT", "INTO", "IS", "LEVEL", "LIKE",
				"LOCK", "LONG", "MAXEXTENTS", "MINUS", "MODE", "MODIFY", "NOAUDIT", "NOCOMPRESS", "NOT", "NOWAIT",
				"NULL", "NUMBER", "OF", "OFFLINE", "ON", "ONLINE", "OPTION", "OR", "ORDER", "PCTFREE", "PRIOR",
				"PRIVILEGES", "PUBLIC", "RAW", "RENAME", "RESOURCE", "REVOKE", "ROW", "ROWS", "ROWID", "ROWNUM",
				"ROWS", "SELECT", "SESSION", "SET", "SHARE", "SETUSER", "SIZE", "SMALLINT", "START", "SUCCESSFUL",
				"SYNONYM", "SYSDATE", "TABLE", "THEN", "TO", "TRIGGER", "UID", "UNION", "UNIQUE", "UPDATE",
				"VALIDATE", "VALUES", "VARCHAR", "VIEW", "WHENEVER", "WHERE", "WITH"]
	if name.upper() in reserved:
		return pfchar + name
	return name

# #
# Tries to reduce sqlname into length
# #
def nameRedutor(name, length):

	newName = ''

	#name = reservedName(name, pfchar)

	counter = 0
	for char in name:
		if counter < 3 and char != char.upper():
			newName += char
			counter += 1
		elif char == char.upper() and char != '_':
			newName += char
			counter = 1
		elif char == '_':
			newName += char
			counter = 0

	if len(newName) <= length:
		return newName
	return name

# #
# Reads XML file with comments
# #
def xmlReader(path):
	with open(path, 'r') as f:
		tree = ET.parse(f, parser=ET.XMLParser(target=myTreeBuilder.myTreeBuilder()))
	return tree.getroot()

def writeToFile(fileName,data):
	if not os.path.exists('output'):
		os.makedirs('output')

	if os.path.isfile('./output/' + fileName):
		while True:
			answer = raw_input('File ' + fileName + ' already exists, overwrite (Y/N): ')
			if 'Y' in answer.upper():
				fileName = './output/' + fileName
				file = open(fileName, 'wb')
				file.write(data)
				file.close()
				print 'File ' + fileName + ' was overwrited.'
				return

			elif 'N' in answer.upper():
				print 'Data was discarded.'
				return
			else:
				print 'Answer not in the rigth format'
	else:
		fileName = './output/' + fileName
		file = open(fileName, 'wb')
		file.write(data)
		file.close()
		print 'File ' + fileName + ' was created.'

def writeToXML(fileName,tree):
	if not os.path.exists('output'):
		os.makedirs('output')

	if os.path.isfile('./output/' + fileName):
		while True:
			answer = raw_input('File ' + fileName + ' already exists, overwrite (Y/N): ')
			if 'Y' in answer.upper():
				fileName = './output/' + fileName
				file = open(fileName, 'w')
				tree.write(file, xml_declaration=True, encoding='utf-8', method="xml")
				file.close()
				print 'File ' + fileName + ' was overwrited.'
				return

			elif 'N' in answer.upper():
				print 'Data was discarded.'
				return
			else:
				print 'Answer not in the rigth format'
	else:
		fileName = './output/' + fileName
		file = open(fileName, 'w')
		tree.write(file, xml_declaration=True, encoding='utf-8', method="xml")
		file.close()
		print 'File ' + fileName + ' was created.'

def writeStringToXML(fileName,root):
	if not os.path.exists('output'):
		os.makedirs('output')

	if os.path.isfile('./output/' + fileName):
		while True:
			answer = raw_input('File ' + fileName + ' already exists, overwrite (Y/N): ')
			if 'Y' in answer.upper():
				fileName = './output/' + fileName
				xml_string = re.sub(r'[\n|\t|\r]', '', ET.tostring(root, encoding='utf-8', method='xml'))
				dom = minidom.parseString(xml_string)
				pretty = unescape(dom.toprettyxml(indent='\t', encoding='utf-8'), {"&apos;": "'", "&quot;": '"', "&amp;": ""})
				pretty = re.sub(r'\&|\&amp;|\&\#38;|\\0026', '', pretty)
				with open(fileName, 'wb') as file:
					file.write(pretty)
				file.close()
				print 'File ' + fileName + ' was overwrited.'
				return

			elif 'N' in answer.upper():
				print 'Data was discarded.'
				return
			else:
				print 'Answer not in the rigth format'
	else:
		fileName = './output/' + fileName
		xml_string = re.sub(r'[\n|\t]', '', ET.tostring(root, encoding='utf-8', method='xml'))
		dom = minidom.parseString(xml_string)
		pretty = unescape(dom.toprettyxml(indent='\t', encoding='utf-8'), {"&apos;": "'", "&quot;": '"'})
		with open(fileName, 'wb') as file:
			file.write(pretty)
		file.close()
		print 'File ' + fileName + ' was created.'

def writeOperationToXML(fileName,root):
	if not os.path.exists('output'):
		os.makedirs('output')

	if os.path.isfile('./output/' + fileName):
		while True:
			answer = raw_input('File ' + fileName + ' already exists, overwrite (Y/N): ')
			if 'Y' in answer.upper():
				fileName = './output/' + fileName
				xml_string = re.sub(r'[\n|\t]', '', ET.tostring(root, encoding='utf-8', method='xml'))
				dom = minidom.parseString(xml_string)
				pretty = dom.toprettyxml(indent='\t', encoding='utf-8')
				with open(fileName, 'wb') as file:
					file.write(pretty)
				file.close()
				print 'File ' + fileName + ' was overwrited.'
				return

			elif 'N' in answer.upper():
				print 'Data was discarded.'
				return
			else:
				print 'Answer not in the rigth format'
	else:
		fileName = './output/' + fileName
		file = open(fileName, 'w')
		xml_string = re.sub(r'[\n|\t]', '', ET.tostring(root, encoding='utf-8', method='xml'))
		dom = minidom.parseString(xml_string)
		pretty = dom.toprettyxml(indent='\t', encoding='utf-8')
		with open(fileName, 'wb') as file:
			file.write(pretty)
		file.close()
		print 'File ' + fileName + ' was created.'

# #
# Verifies if argument is number or not
# #
def isDigit(argument):
	try:
		float(argument)
		return True
	except ValueError:
		pass

	try:
		import unicodedata
		unicodedata.numeric(argument)
		return True
	except (TypeError, ValueError):
		pass

	return False

# #
# Validates consistency of client data and, if needed, applies some corrections
# #
def validateInformation(info, catalogType, vendor, dataRules=None, enumList=list()):
	vendor = vendor.upper()
	if vendor == 'NOKIA':
		vendor = 'NSN'

	configuration = json.load(open('./lib/configuration.json'))
	if 'addPrefix' in dataRules['unit']:
		for cfg in dataRules['unit']['addPrefix']:
			if cfg['field'] == 'sqlName':
				configuration['unit']['sqlName']['maxLength'] = int(configuration['unit']['sqlName']['maxLength']) - len(cfg['value'])

	if 'addPrefix' in dataRules['item']:
		for cfg in dataRules['item']['addPrefix']:
			if cfg['field'] == 'sqlName':
				configuration['item']['sqlName']['maxLength'] = int(
					configuration['item']['sqlName']['maxLength']) - len(cfg['value'])

	if vendor not in configuration['unit']['sqlName']:
		vendor = 'GENERIC'

	# UNIT VALIDATIONS #
	for unitId in info.keys():
		unitInfo = info[unitId]['attributes']

		# Validate tableName
		if vendor == 'HUAWEI' and unitInfo['tableName'].endswith('.0'):
			unitInfo['tableName'] = unitInfo['tableName'].replace('.0', '')
		tmpUnitData = validateSqlName(unitInfo['tableName'], configuration['unit']['sqlName']['regexUnwantedChar'], int(configuration['unit']['sqlName']['maxLength']), configuration['unit']['sqlName'][vendor]['char'][catalogType])
		if tmpUnitData != unitInfo['tableName'] and validateUnique(info[unitId]['items'], 'tableName', tmpUnitData):
			unitInfo['tableName'] = tmpUnitData

		# Validate name
		unitInfo['name'] = re.sub(r'\&', '', unitInfo['name'])

		# Validate udn
		tmpUnitData = validateUdn(unitInfo['udn'])
		if tmpUnitData != unitInfo['udn']:
			unitInfo['udn'] = tmpUnitData

		# Validate description
		tmpUnitData = validateDescription(unitInfo['desc'])
		if unitInfo['desc'] == '':
			unitInfo['desc'] = unitInfo['name']
		if tmpUnitData != unitInfo['desc']:
			unitInfo['desc'] = tmpUnitData

		# ITEM VALIDATIONS #
		for itemId in info[unitId]['items'].keys():
			itemInfo = info[unitId]['items'][itemId]
			# Validate bdcolname
			if vendor == 'HUAWEI' and itemInfo['bdcolname'].endswith('.0'):
				itemInfo['bdcolname'] = itemInfo['bdcolname'].replace('.0', '')
			tmpItemData = validateSqlName(itemInfo['bdcolname'], configuration['item']['sqlName']['regexUnwantedChar'], int(configuration['item']['sqlName']['maxLength']), configuration['item']['sqlName'][vendor]['char'][catalogType])
			if tmpItemData != itemInfo['bdcolname'] and validateUnique(info[unitId]['items'], 'bdcolname', tmpItemData):
				itemInfo['bdcolname'] = tmpItemData

			# Validate name
			itemInfo['name'] = re.sub(r'\&', '', itemInfo['name'])

			# Validate udn
			tmpItemData = validateUdn(itemInfo['udn'])
			if tmpItemData != itemInfo['udn'] and validateUnique(info[unitId]['items'], 'udn', tmpItemData):
				itemInfo['udn'] = tmpItemData

			# Validate description
			tmpItemData = validateDescription(itemInfo['desc'])
			if itemInfo['desc'] == '':
				itemInfo['desc'] = itemInfo['name']
			if tmpItemData != itemInfo['desc']:
				itemInfo['desc'] = tmpItemData

			# Validate bdtype
			itemInfo['bdtype'] = validateFieldType(itemInfo['bdtype'], configuration['item']['bdtype'], 'VARCHAR2(256)', enumList)
			
			# Validate typeCust
			if itemInfo['dataType'] != '':
				itemInfo['typeCust'] = validateFieldType(itemInfo['dataType'], configuration['item']['typeCust'], 'STRING', enumList)
			else:
				itemInfo['typeCust'] = validateFieldType(itemInfo['bdtype'], configuration['item']['typeCust'], 'STRING', enumList)
			
			if itemInfo['typeCust'].__contains__('VARCHAR'):
				itemInfo['typeCust'] = 'STRING'

			# Validate dbn0type
			if 'dbn0type' not in itemInfo:
				if catalogType == 'CM':
					itemInfo['dbn0type'] = 'CM'
				elif catalogType == 'PM':
					if (('VARCHAR2(' in itemInfo['bdtype'] or 'TIMESTAMP(' in itemInfo['bdtype'])
							and itemInfo['dataType'] not in configuration['item']['dbn0typePDF']):
						itemInfo['dbn0type'] = 'ID'
					else:
						itemInfo['dbn0type'] = 'MT'
				else:
					itemInfo['dbn0type'] = 'N/A'
	return info

# #
# Validates the description and removes unwanted chars
# #
def validateDescription(desc):
	desc = re.sub(r'((\t)|(\n)|(\r)|(\\r)|(\\n)|((&|\#).*;)|\<|\>|&|<n>)', '', desc)
	if re.match(r'((\t)|(\n)|(\r)|(\\r)|(\\n)|((&|#).*;)|\<|\>|&|(  )|<n>)', desc):
		desc = removeSpaces(re.sub(r'((\t)|(\n)|(\r)|(\\r)|(\\n)|((&|\#).*;)|\<|\>|&|<n>)', '', desc))
	return desc

# #
# Change all duple spaces to one space
# #
def removeSpaces(desc):
	if re.match(r'  ', desc):
		return removeSpaces(re.sub(r'  ', ' ', desc))
	return desc

# #
# Validates sqlname, given the name and the maximum number of chars, and the prefix char to be added if name is number
# It also removes unwanted chars
# #
def validateSqlName(name, regexUnwantedChar = '', maxSize = 30, pfChar = 'C'):
	#return name
	#Necessita de validacoes futuras

	name = re.sub(regexUnwantedChar, '', name)
	name = re.sub(r'(\[|\]|\(|\)|-|/|\.|\,|\<|\>| |%|\&|\+)', '', name)

	#print 'name= ' + str(name)
	try:
		if isDigit(name[0]):
			name = pfChar + name
		else:
			name = reservedName(name, pfChar)
	except:
		print 'name= ' + str(name)
		return name

	if len(name) > maxSize:
		return nameRedutor(name, maxSize)
	return name

# #
# Validates udn and removes unwanted chars
# #
def validateUdn(udn):

	return re.sub(r'(\[|\]|\(|\)|-|/|\,|\&| |\<|\>|:|=|%|\+)', '', udn)

# #
# Validates bdtype/typeCust and converts to correspondent value in configuration.json
# If doesnt exist in configuration.json creates with elseType
# #
def validateFieldType(fieldType, typeConverter, elseType, enumList):
	if fieldType.upper().split('[')[0] in enumList:
		return elseType

	if fieldType.upper().startswith("VARCHAR2(") and fieldType.upper().endswith(")"):
		try:
			int(fieldType.upper()[9:-1])
			return fieldType.upper()
		except ValueError:
			pass
	elif fieldType.upper().startswith("VARCHAR(") and fieldType.upper().endswith(")"):
		try:
			vchar = int(fieldType.upper()[8:-1])
			return "VARCHAR2("+str(vchar)+")"
		except ValueError:
			pass

	for key in typeConverter.keys():
		if (fieldType.upper()).startswith(key):
			return typeConverter[key]
	return elseType

def validateUnique(dataDict, field, value):

	for key in dataDict.keys():
		try:
			if dataDict[key][field] == value:
				return False
		except:
			pass
	return True