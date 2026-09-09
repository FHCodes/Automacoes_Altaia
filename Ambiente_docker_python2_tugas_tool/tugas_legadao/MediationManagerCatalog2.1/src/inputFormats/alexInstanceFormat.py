__doc__ = \
	__version__ = '1.1'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

import lxml.html as html
from lib.functions import *
from collections import OrderedDict
import copy
import xml.etree.ElementTree as ET
import os
import re

def copy_catalog_html(filepath):
	sampleTree = html.parse(filepath)
	root = sampleTree.getroot()
	return root


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


def processData(root, pmGroupSheet, measurementTypeSheet, positions, header, path):
	state = False
	try:
		head = root.find('head').find('title')
		# print head.text
		if 'MIB' in head.text.split(' ')[0].upper():
			# Structure
			try:
				positions, header = getInstance(root.find('body'), pmGroupSheet, measurementTypeSheet, positions, header, path)
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

	return (positions, state, header)


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


# #
# Gets fields names and values from table
# #
def getFields(elem):
	document = dict()
	for tr in elem.findall('tr'):
		name = ""
		value = ""
		for td in tr.findall('td'):
			if name == "":
				name = getText(td).strip()
			else:
				value = getText(td).strip()
		if 'keyName' in name:
			if value.upper() == 'SUM':
				continue
			document[name] = value
			document['dbn0type'] = 'ID'
			if 'ossId' not in document.keys():
				document['ossId'] = value
			else:
				document['ossId'] = '{0}{1}'.format(document['ossId'], value)
		else:
			document[name] = value
			document['dbn0type'] = 'MT'
	return document

# #
# Gets the data from the instances
# #
def getInstance(root, pmGroupSheet, measurementTypeSheet, positions, header, path):
	(pg, mt) = positions

	dataType = None
	unitDocumentsList = list()
	counterDocumentsList = list()
	unitList = list()

	for elem in root:
		if elem.tag == 'a':
			if elem.text == 'PmGroup':
				dataType = 'PmGroup'
			elif elem.text == 'MeasurementType':
				dataType = 'MeasurementType'

		elif elem.tag == 'table':
			if dataType == 'PmGroup':
				body = elem.find('tbody')
				unitDocument = getFields(body)
				unitDocument['ossId'] = unitDocument['pmGroupId']
				for key in unitDocument.keys():
					if key not in header['unit'].keys():
						header['unit'][key] = len(header['unit'].keys())
				unitDocumentsList.append(unitDocument)
				unitList.append(unitDocument['pmGroupId'])

			elif dataType == 'MeasurementType':
				body = elem.find('tbody')
				counterDocument = getFields(body)
				counterDocument['pmGroupId'] = unitDocument['pmGroupId']
				if 'ossId' in counterDocument.keys():
					counterDocument['ossId'] = '{0}_{1}'.format(unitDocument['pmGroupId'], counterDocument['ossId'])
					tmp = dict()
					if counterDocument['ossId'] not in unitList:
						tmp = copy.deepcopy(unitDocument)
						tmp['pmGroupId'] = counterDocument['ossId']
						tmp['description'] = counterDocument['ossId']
						unitDocumentsList.append(tmp)
						unitList.append(counterDocument['ossId'])
				else:
					counterDocument['ossId'] = unitDocument['pmGroupId']
				measuredObjectId = ''
				for key in counterDocument.keys():
					if key not in header['counter'].keys():
						header['counter'][key] = len(header['counter'].keys())
					if 'keyName' in key:
						tmp = dict()
						tmp['measurementTypeId'] = (key if '[' not in key else re.sub(r'\[|\]|0', '', key))
						measuredObjectId = '{:s}{:s}{:s}'.format(measuredObjectId, ('' if measuredObjectId == '' else '-'), tmp['measurementTypeId'])
						tmp['measurementName'] = counterDocument[key]
						tmp['collectionMethod'] = 'STRING'
						tmp['description'] = counterDocument[key]
						tmp['dbn0type'] = 'ID'
						tmp['ossId'] = counterDocument['ossId']
						tmp['pmGroupId'] = counterDocument['pmGroupId']
						counterDocumentsList.append(tmp)
				tmp = unitDocumentsList[-1]
				if measuredObjectId != '':
					tmp['measurementObject'] = measuredObjectId
				unitDocumentsList[-1] = tmp
				counterDocumentsList.append(counterDocument)


	for unitDocument in unitDocumentsList:
		data = list()
		for key in header['unit'].keys():
			if key in unitDocument.keys():
				data.append(unitDocument[key])
			else:
				data.append('')
		pmGroupSheet = writeToSheet(pmGroupSheet, data, pg, False)
		pg += 1

	for counterDocument in counterDocumentsList:
		data = list()
		for key in header['counter'].keys():
			if key in counterDocument.keys():
				data.append(counterDocument[key])
			else:
				data.append('')
		if data[4] in [None, '']:
			continue
		measurementTypeSheet = writeToSheet(measurementTypeSheet, data, mt, False)
		mt += 1

	return (pg, mt), header

def writeFamilyToCSV(fileName, header, data):
	if os.path.isfile(fileName):
		file = open(fileName, 'a')
	else:
		file = open(fileName, 'w')
		file.write(header)
	file.write(data)
	file.close()

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
	file = path + 'alexdoc.html'
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
			transform(fileName, path)
			print '-> Finish processing alx.'
			return fileName
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

	pmGroupSheet = createSheet(workbook, 'PmGroup')
	measurementTypeSheet = createSheet(workbook, 'MeasurementType')

	positions = (1, 1)

	inputName = raw_input('Nomenclature of file: ')
	header = OrderedDict()
	header['unit'] = OrderedDict()
	header['unit']['measurementObject'] = 0
	header['counter'] = OrderedDict()

	for file in fileList:
		if inputName in file:
			# fileProcess(file)
			# print file
			root = copy_catalog_html(file)
			positions, state, header = processData(root, pmGroupSheet, measurementTypeSheet, positions, header, path)
			if state:
				os.remove(file)
		elif not ('.html' in file):
			print '[REMOVED]: ' + file
			os.remove(file)
			pass

	pmGroupSheet = writeToSheet(pmGroupSheet, header['unit'].keys(), 0, True)
	measurementTypeSheet = writeToSheet(measurementTypeSheet, header['counter'].keys(), 0, True)
	writeToExcel(fileName, workbook)
