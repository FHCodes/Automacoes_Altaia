__doc__ = \
	__version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

from lib.objects.column import column

# #
# If in all patterns exists the level creates it, from high hierarchy level to low
# #
def process(unitDict, config):

	dataList = processList(getList(unitDict))

	for ossId in unitDict.keys():
		unitObj = unitDict[ossId]

		if dataList[unitObj.typeId]['Cell']:

				columnObj = column()
				columnObj.create('NODEB_NAME', 'NODEB_NAME', 'NODEB_NAME', 'NODEB_NAME', 'NODEB_NAME', 'ID', 'VARCHAR2(256)', 'STRING', 'STRING', 'N/A', '')
				unitObj.addAttribute('NODEB_NAME', columnObj)

				columnObj = column()
				columnObj.create('CELL_ID', 'CELL_ID', 'CELL_ID', 'CELL_ID', 'CELL_ID', 'ID', 'VARCHAR2(256)', 'STRING', 'STRING', 'N/A', '')
				unitObj.addAttribute('CELL_ID', columnObj)

				columnObj = column()
				columnObj.create('CELL_NAME', 'CELL_NAME', 'CELL_NAME', 'CELL_NAME', 'CELL_NAME', 'ID', 'VARCHAR2(256)', 'STRING', 'STRING', 'N/A', '')
				unitObj.addAttribute('CELL_NAME', columnObj)

		elif dataList[unitObj.typeId]['NodeB']:
			columnObj = column()
			columnObj.create('NODEB_NAME', 'NODEB_NAME', 'NODEB_NAME', 'NODEB_NAME', 'NODEB_NAME', 'ID', 'VARCHAR2(256)', 'STRING', 'STRING', 'N/A', '')
			unitObj.addAttribute('NODEB_NAME', columnObj)

def getList(unitDict):

	dataDict = dict()

	for ossId in unitDict.keys():
		unitObj = unitDict[ossId]
		dataDict[unitObj.typeId] = dict()
		dataDict[unitObj.typeId]['measObjs'] = dict()
		try:
			dataDict[unitObj.typeId]['isStruct'] = unitObj.isStruct
		except:
			dataDict[unitObj.typeId]['isStruct'] = False
		dataDict[unitObj.typeId]['Cell'] = False
		dataDict[unitObj.typeId]['NodeB'] = False
		toCell = True
		toNodeB = True
		for measObj in (unitObj.measuredObject.upper().replace(' ','')).split(','):
			dataDict[unitObj.typeId]['measObjs'][measObj] = dict()
			dataDict[unitObj.typeId]['measObjs'][measObj]['objList'] = measObj.split('-')
			del dataDict[unitObj.typeId]['measObjs'][measObj]['objList'][-1]

			if 'UTRANCELL' in dataDict[unitObj.typeId]['measObjs'][measObj]['objList'] or 'RBSLOCALCELL' in dataDict[unitObj.typeId]['measObjs'][measObj]['objList']:
				dataDict[unitObj.typeId]['measObjs'][measObj]['hasCell'] = True
				dataDict[unitObj.typeId]['Cell'] = True
			elif not dataDict[unitObj.typeId]['isStruct']:
				dataDict[unitObj.typeId]['measObjs'][measObj]['hasCell'] = False
				toCell = False

			if 'NODEBFUNCTION' in dataDict[unitObj.typeId]['measObjs'][measObj]['objList']:
				dataDict[unitObj.typeId]['measObjs'][measObj]['hasNodeB'] = True
				dataDict[unitObj.typeId]['NodeB'] = True
			elif not dataDict[unitObj.typeId]['isStruct']:
				dataDict[unitObj.typeId]['measObjs'][measObj]['hasNodeB'] = False
				toNodeB = False

		if len(dataDict[unitObj.typeId]['measObjs'].keys()) > 0 and not dataDict[unitObj.typeId]['isStruct']:
			if toCell:
				dataDict[unitObj.typeId]['Cell'] = True
			if toNodeB:
				dataDict[unitObj.typeId]['NodeB'] = True

	return dataDict

def processList(dataList):

	for n in dataList.keys():
		for key in dataList.keys():
			if dataList[key]['Cell'] or dataList[key]['NodeB']:
				continue

			toCell = True
			toNodeB = True
			for measObj in dataList[key]['measObjs'].keys():
				for objKey in dataList[key]['measObjs'][measObj]['objList']:
					if objKey in dataList.keys():
						if dataList[objKey]['Cell']:
							dataList[key]['measObjs'][measObj]['hasCell'] = True
							if dataList[key]['isStruct']:
								dataList[key]['Cell'] = True
							break

						if dataList[objKey]['NodeB']:
							dataList[key]['measObjs'][measObj]['hasNodeB'] = True
							if dataList[key]['isStruct']:
								dataList[key]['NodeB'] = True
							break

				if not dataList[key]['isStruct']:
					if not dataList[key]['measObjs'][measObj]['hasCell']:
						toCell = False
					if not dataList[key]['measObjs'][measObj]['hasNodeB']:
						toNodeB = False

			if len(dataList[key]['measObjs'].keys()) > 0 and not dataList[key]['isStruct']:
				if toCell:
					dataList[key]['Cell'] = True
				if toNodeB:
					dataList[key]['NodeB'] = True

	return dataList