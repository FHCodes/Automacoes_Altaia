__doc__ = \
	__version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

import os
import json
import re

def validateInformation(vendor, catalogType, info):
	vendor = vendor.upper()
	if vendor == 'NOKIA':
		vendor = 'NSN'

	configuration = json.load(open('./lib/configuration.json'))

	if vendor not in configuration['unit']['sqlName']:
		vendor = 'GENERIC'

	# UNIT VALIDATIONS #
	for unitId in info.keys():
		unitInfo = info[unitId]['attributes']

		# Validate tableName
		tmpUnitData = validateSqlName(unitInfo['tableName'], configuration['unit']['sqlName']['regexUnwantedChar'], int(configuration['unit']['sqlName']['maxLength']), configuration['unit']['sqlName'][vendor]['char'][catalogType])
		if tmpUnitData != unitInfo['tableName'] and tmpUnitData not in info.keys():
			unitInfo['tableName'] = tmpUnitData

		# Validate udn
		tmpUnitData = validateUdn(unitInfo['udn'])
		if tmpUnitData != unitInfo['udn']:
			unitInfo['udn'] = tmpUnitData

		# Validate description
		tmpUnitData = validateDescription(unitInfo['desc'])
		if tmpUnitData != unitInfo['desc']:
			unitInfo['desc'] = tmpUnitData

		# ITEM VALIDATIONS #
		for itemId in info[unitId]['items'].keys():
			itemInfo = info[unitId]['items'][itemId]
			# Validate bdcolname
			tmpItemData = validateSqlName(itemInfo['bdcolname'], configuration['item']['sqlName']['regexUnwantedChar'], int(configuration['item']['sqlName']['maxLength']), configuration['item']['sqlName'][vendor]['char'][catalogType])
			if tmpItemData != itemInfo['bdcolname'] and tmpItemData not in info[unitId]['items'].keys():
				itemInfo['bdcolname'] = tmpItemData

			# Validate udn
			tmpItemData = validateUdn(itemInfo['udn'])
			if tmpItemData != itemInfo['udn']:
				itemInfo['udn'] = tmpItemData

			# Validate description
			tmpItemData = validateDescription(itemInfo['desc'])
			if tmpItemData != itemInfo['desc']:
				itemInfo['desc'] = tmpItemData

			# Validate bdtype
			itemInfo['bdtype'] = validateFieldType(itemInfo['bdtype'], configuration['item']['bdtype'], 'VARCHAR2(256)')
			# Validate typeCust
			itemInfo['typeCust'] = validateFieldType(itemInfo['dataType'], configuration['item']['typeCust'], 'STRING')

			# Validate dbn0type
			if 'dbn0type' not in itemInfo:
				if catalogType == 'CM':
					itemInfo['dbn0type'] = 'CM'
				elif 'VARCHAR2(' in itemInfo['bdtype'] or 'TIMESTAMP(' in itemInfo['bdtype']:
					itemInfo['dbn0type'] = 'ID'
				elif catalogType == 'PM':
					itemInfo['dbn0type'] = 'MT'
				else:
					itemInfo['dbn0type'] = 'N/A'
	return info

def validateDescription(desc):
	desc = re.sub(r'((\t)|(\n)|(\r)|(\\r)|(\\n)|((&|\#).*;)|&|\<|\>|\")', '', desc)
	if re.match(r'((\t)|(\n)|(\r)|(\\r)|(\\n)|((&|#).*;)|&|(  )|\<|\>|\")', desc):
		desc = removeSpaces(re.sub(r'((\t)|(\n)|(\r)|(\\r)|(\\n)|((&|\#).*;)|&)|\<|\>|\"', '', desc))
	return desc

def removeSpaces(desc):
	if re.match(r'  ', desc):
		return removeSpaces(re.sub(r'  ', ' ', desc))
	return desc

def validateSqlName(name, regexUnwantedChar = '', maxSize = 30, pfChar = 'C'):
	#return name
	#Necessita de validacoes futuras

	name = re.sub(regexUnwantedChar, '', name)
	name = re.sub(r'(\[|\]|\(|\)|-|/|\.|\,| |%|\<|\>)', '', name)

	if isDigit(name):
		name = pfChar + name
	else:
		name = reservedName(name, pfChar)

	if len(name) > maxSize:
		return nameRedutor(name, maxSize)
	return name

def validateUdn(udn):

	return re.sub(r'(\[|\]|\(|\)|-|/|\,| |:|=|%|\<|\>)', '', udn)

def validateFieldType(fieldType, typeConverter, elseType):
	for key in typeConverter.keys():
		if (fieldType.upper()).startswith(key):
			return typeConverter[key]
	return elseType


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
