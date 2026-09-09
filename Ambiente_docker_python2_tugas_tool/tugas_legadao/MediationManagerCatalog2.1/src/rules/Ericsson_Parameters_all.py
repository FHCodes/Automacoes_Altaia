__doc__ = \
	__version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

from xml.etree.cElementTree import Element
import xml.etree.cElementTree as ET
from lib.objects.column import column

# #
# If in one pattern exists the level creates it, from high hierarchy level to low
# #
def process(unitDict, config):

	dataList = processList(getList(unitDict))

	for unitId in unitDict.keys():
		unitObj = unitDict[unitId]
		if dataList[unitObj.typeId]['Cell']:
			if 'NODEB_NAME' not in unitObj.bdcolnames:
				attr = column()
				attr.create('NODEB_NAME', 'NODEB_NAME', 'NODEB_NAME', 'NODEB_NAME', 'NODEB_NAME', 'ID', 'VARCHAR2(256)', 'STRING', 'STRING', 'N/A', '')
				unitObj.addAttribute(attr)
			if 'CELL_ID' not in unitObj.bdcolnames:
				attr = column()
				attr.create('CELL_ID', 'CELL_ID', 'CELL_ID', 'CELL_ID', 'CELL_ID', 'ID', 'VARCHAR2(256)', 'STRING', 'STRING', 'N/A', '')
				unitObj.addAttribute(attr)
			if 'CELL_NAME' not in unitObj.bdcolnames:
				attr = column()
				attr.create('CELL_NAME', 'CELL_NAME', 'CELL_NAME', 'CELL_NAME', 'CELL_NAME', 'ID', 'VARCHAR2(256)', 'STRING', 'STRING', 'N/A', '')
				unitObj.addAttribute(attr)

		elif dataList[unitObj.typeId]['NodeB']:
			if 'NODEB_NAME' not in unitObj.bdcolnames:
				attr = column()
				attr.create('NODEB_NAME', 'NODEB_NAME', 'NODEB_NAME', 'NODEB_NAME', 'NODEB_NAME', 'ID', 'VARCHAR2(256)', 'STRING', 'STRING', 'N/A', '')
				unitObj.addAttribute(attr)

def getList(unitDict):
	dataDict = dict()
	for unitId in unitDict.keys():
		unitObj = unitDict[unitId]
		dataDict[unitObj.typeId] = dict()
		dataDict[unitObj.typeId]['measObjs'] = dict()
		dataDict[unitObj.typeId]['Cell'] = False
		dataDict[unitObj.typeId]['NodeB'] = False
		for measObj in (unitObj.measuredObject.upper().replace(' ','')).split(','):
			dataDict[unitObj.typeId]['measObjs'][measObj] = measObj.split('-')
			if 'UTRANCELL' in dataDict[unitObj.typeId]['measObjs'][measObj] or 'RBSLOCALCELL' in dataDict[unitObj.typeId]['measObjs'][measObj]:
				dataDict[unitObj.typeId]['Cell'] = True
				break

			elif 'NODEBFUNCTION' in dataDict[unitObj.typeId]['measObjs'][measObj]:
				dataDict[unitObj.typeId]['NodeB'] = True
				break

	return dataDict

def processList(dataList):

	for n in dataList.keys():
		for key in dataList.keys():
			if dataList[key]['Cell']:
				continue

			for measObj in dataList[key]['measObjs'].keys():
				for objKey in dataList[key]['measObjs'][measObj]:
					if objKey in dataList.keys():
						if dataList[objKey]['Cell']:
							dataList[key]['Cell'] = True
							break

						elif dataList[objKey]['NodeB']:
							dataList[key]['NodeB'] = True
							break

	return dataList