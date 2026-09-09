__doc__ = \
	__version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

import os, re, json
from lib.functions import xmlReader
from lib.objects.unit import unit
from lib.objects.table import table
from lib.objects.column import column
from lib.objects.hierarchy import hierarchy
from lib.Logger import Logger

# #
# Gets "historic" from shelf versions or from catalog path passed
# #
def getVersioningHistoric(vendor, collectorName, shelfPath):
	data = dict()

	if shelfPath.upper() == 'NA':
		return data

	elif shelfPath.startswith("C:/"):
		if shelfPath.endswith('.xml'):
			clientRoot = xmlReader(shelfPath.replace('#', 'client'))
			ossRoot = xmlReader(shelfPath.replace('#', 'oss'))
			operationsRoot = xmlReader(shelfPath.replace('#', 'operations'))

			data, matchId = getCientStruct(clientRoot, data)
			data = getOssStruct(ossRoot, data)
			data = getOperationsStruct(operationsRoot, data, matchId)
		elif shelfPath.endswith('.json'):
			getLoadingCatalog(shelfPath)
		else:
			print 'No file extension, that was acceptable, found'
	else:
		path = '../../../../trunk/conf/catalogos/collectorProcess/Catalogs/{:s}/Product_Packs_Shelf/{:s}/'.format(vendor, collectorName)
		versionsList = [os.path.join(path, o) for o in os.listdir(path) if os.path.isdir(os.path.join(path, o))]
		for version in versionsList:
			clientRoot = None
			ossRoot = None
			operationsRoot = None
			versionFiles = [f for f in os.listdir(version) if os.path.isfile(os.path.join(version, f))]
			for file in versionFiles:
				if re.search(r'_client.*.xml', file) is not None:
					clientRoot = xmlReader(version + '/' + file)
				elif re.search(r'_oss.*.xml', file) is not None:
					ossRoot = xmlReader(version + '/' + file)
				elif re.search(r'_operations.*.xml', file) is not None:
					operationsRoot = xmlReader(version + '/' + file)


			data, matchId = getCientStruct(clientRoot, data)
			data = getOssStruct(ossRoot, data)
			data = getOperationsStruct(operationsRoot, data, matchId)

	return data

# #
# Gets XML catalogs data from catalogPath
# #
def getCatalog(catalogPath):
	data = dict()

	clientRoot = xmlReader(catalogPath.replace('#', 'client'))
	data, matchId = getCientStruct(clientRoot, data)
	ossRoot = xmlReader(catalogPath.replace('#', 'oss'))
	data = getOssStruct(ossRoot, data)
	operationsRoot = xmlReader(catalogPath.replace('#', 'operations'))
	data = getOperationsStruct(operationsRoot, data, matchId)

	return data

# #
# Reads and converts client catalog data to program acceptable data format
# #
def getCientStruct(root, data):
	logger = Logger('processLogger').get()
	matchId = dict()

	for tableXml in root.findall('table'):
		ossId = tableXml.get('ossId')
		if ossId not in data.keys():
			unitObj = unit()
			unitObj.create(ossId, tableXml.get('id'), '', '', '')
			unitObj.tech = tableXml.get('tech')
			data[ossId] = unitObj
		else:
			unitObj = data[ossId]

		tableId = tableXml.get('id')
		if tableId in unitObj.tables.keys():
			tableObj = unitObj.tables[tableId]
			pass
		else:
			matchId[tableId] = ossId
			tableObj = table()
			tableObj.create(tableId, ossId, tableXml.get('tableName'), tableXml.get('udn'))
			if re.search(ossId + '_(\d+)$', tableId) is not None:
				tableObj.partitionOf = ossId
			unitObj.addTable(tableId.upper(), tableObj)

		for columnXml in tableXml.findall('column'):
			columnId = columnXml.get('id')
			if columnId in tableObj.counters.keys():
				logger.warning(' * [versioningLoader] Duplicated column id \"{:s}\" was found on table \"{:s}\" * '.format(columnId, tableId))
				continue
			columnObj = column()
			columnObj.create(columnId, '', columnXml.get('udn'), columnXml.get('bdcolname'), '', columnXml.get('dbn0type'), columnXml.get('bdtype'), '', '', '', 0)
			if columnObj.dbn0type in ['PK', 'ID']:
				unitObj.addAttribute(columnId, columnObj)
			else:
				tableObj.addCounter(columnId, columnObj)
	return data, matchId

# #
# Reads and converts oss catalog data to program acceptable data format
# #
def getOssStruct(root, data):
	logger = Logger('processLogger').get()
	#measuredobjects
	for unitXml in root.findall('unit'):
		ossId = unitXml.get('ossId')
		if ossId not in data.keys():
			logger.error(' * [versioningLoader] ossId \"{:s}\" was not found in client catalog. * '.format(ossId))
		else:
			unitObj = data[ossId]
			unitObj.measuredObject = unitXml.get('measuredobjects')
			unitObj.name = unitXml.get('name')
			unitObj.desc = unitXml.get('desc')

			tableList = unitObj.tables
			for itemXml in unitXml.findall('item'):
				itemId = itemXml.get('id')
				if itemId in unitObj.attributes.keys():
					counterObj = unitObj.attributes[itemId]
					counterObj.name = itemXml.get('name')
					counterObj.desc = itemXml.get('desc')
					counterObj.typeCust = itemXml.get('typeCust')
					counterObj.typeVendor = itemXml.get('typeVendor')
					counterObj.unitVendor = itemXml.get('unitVendor')
					continue

				isMissing = True
				for tableId in tableList.keys():
					tableObj = tableList[tableId]
					if itemId in tableObj.counters.keys():
						isMissing = False
						counterObj = tableObj.counters[itemId]
						counterObj.name = itemXml.get('name')
						counterObj.desc = itemXml.get('desc')
						counterObj.typeCust = itemXml.get('typeCust')
						counterObj.typeVendor = itemXml.get('typeVendor')
						counterObj.unitVendor = itemXml.get('unitVendor')
						break


				if isMissing:
					logger.warning(' * [versioningLoader] itemId \"{:s}\" from ossId \"{:s}\" was not found in client catalog. * '.format(itemId, ossId))
	return data

# #
# Reads and converts operations catalog data to program acceptable data format
# #
def getOperationsStruct(root, data, matchId):
	logger = Logger('processLogger').get()

	for unitXml in root.findall('unit'):
		unitId = unitXml.get('id')

		if unitId in matchId.keys():
			ossId = matchId[unitId]
			unitObj = data[ossId]
			for opXml in unitXml.findall('operation'):
				unitObj.addOperation('unit', unitId, opXml)
			for itemXml in unitXml.findall('item'):
				itemId = itemXml.get('id')
				for opXml in itemXml.findall('operation'):
					unitObj.addOperation('item', itemId, opXml)
	return data

# #
# Reads and converts loading json catalog data to program acceptable data format
# #
def getLoadingCatalog(catalogPath):
	logger = Logger('processLogger').get()

	loadingCatalog = json.load(open(catalogPath))
	data = dict()

	for unitDict in loadingCatalog['measUnits']:
		ossId = unitDict['partitionOf']
		if ossId not in data.keys():
			unitObj = unit()
			unitObj.create(ossId, unitDict['vendorId'], unitDict['name'], unitDict['description'], unitDict['measuredObjects'])
			unitObj.tech = unitDict['tech']
			data[ossId] = unitObj
		else:
			unitObj = data[ossId]

		tableId = unitDict['id']
		if tableId.upper() not in unitObj.tables.keys():
			tableObj = table()
			tableObj.create(tableId, ossId, unitDict['tableName'], unitDict['udn'])
			unitObj.addTable(tableId.upper(), tableObj)
		else:
			tableObj = unitObj.getTable(tableId.upper())

		for itemDict in unitDict['measItems']:
			columnObj = column()
			columnObj.create(itemDict['id'], itemDict['name'], itemDict['udn'], itemDict['columnName'], itemDict['description'], itemDict['measItemType'], itemDict['type'], itemDict['typeCust'], itemDict['typeVendor'], itemDict['unitVendor'], 0)
			if itemDict['measItemType'] in ['PK', 'ID']:
				unitObj.addAttribute(itemDict['id'], columnObj)
				continue
			elif itemDict['measItemType'] in ['MT', 'CM']:
				tableObj.addCounter(itemDict['id'], columnObj)

	return data

# #
# Converts data/catalog to be in coherence with "historic" (previous versions)
# #
def convertData(docData, vendor, collectorName, shelfPath):
	versionData = getVersioningHistoric(vendor, collectorName, shelfPath)

	data = dict()

	#print docData.keys()
	for ossId in docData.keys():
		dUnitObj = docData[ossId]
		#print dUnitObj.tables.keys()
		#print '\n\n\n'

		if ossId in versionData.keys():
			unitObj = unit()
			unitObj.create(ossId, dUnitObj.typeId, dUnitObj.name, dUnitObj.desc, dUnitObj.measuredObject)
			unitObj.tech = dUnitObj.tech
			unitObj.setHierarchy(dUnitObj.hierarchyList)
			unitObj.setOperations(dUnitObj.operations)
			unitObj.attributes = dUnitObj.attributes
			data[ossId] = unitObj

			vUnitObj = versionData[ossId]
			#print vUnitObj.tables.keys()
			#print '\n\n\n\n\n\n\n'

			for attributeId in unitObj.attributes.keys():
				for vAttributeId in vUnitObj.attributes.keys():
					if attributeId == vAttributeId:
						attributeObj = unitObj.getAttribute(attributeId)
						vAttributeObj = vUnitObj.getAttribute(attributeId)
						attributeObj.sqlName = vAttributeObj.sqlName
						attributeObj.udn = vAttributeObj.udn
						attributeObj.name = vAttributeObj.name


			for dTableId in sorted(dUnitObj.tables.keys()):
				dTableObj = dUnitObj.getTable(dTableId)

				for vTableId in sorted(vUnitObj.tables.keys()):
					vTableObj = vUnitObj.getTable(vTableId)
					if re.sub(r'_(\d+)$', '', dTableId) == re.sub(r'_(\d+)$', '', vTableId) or dTableId == vTableId:
						for dCounteId in sorted(dTableObj.counters.keys()):
							dCounteObj = dTableObj.getCounter(dCounteId)
							isNewCounter = True

							for vCounterId in sorted(vTableObj.counters.keys()):
								vCounterObj = vTableObj.getCounter(vCounterId)

								if vCounterId == dCounteId and isNewCounter:
									if vTableId in unitObj.tables.keys():
										tableObj = unitObj.getTable(vTableId)
									else:
										tableObj = table()
										tableObj.create(vTableId, ossId, vTableObj.sqlName, vTableObj.udn)
										unitObj.addTable(vTableId, tableObj)
									dCounteObj.sqlName = vCounterObj.sqlName
									#dCounteObj.udn = vCounterObj.udn
									#dCounteObj.name = vCounterObj.name
									tableObj.addCounter(dCounteId, dCounteObj)
									isNewCounter = False

							if isNewCounter:
								try:
									#print 'NewCounter: ' + dCounteId
									vLastTableId, vLastTableNumber = getLastTablePartition(vUnitObj.tables, (re.sub(r'_(\d+)$', '', dTableId) if re.search(r'_(\d+)$', dTableId) is not None else dTableId))
									vLastTableObj = vUnitObj.getTable(vLastTableId)
									if (vLastTableObj.numberOfCounters + unitObj.numberOfAttributes) < 970:
										if vLastTableId in unitObj.tables.keys():
											vLastTableObj.addCounter(dCounteId, dCounteObj)
											tableObj = unitObj.getTable(vLastTableId)
											tableObj.addCounter(dCounteId, dCounteObj)
											print 'NewCounter: \"{:s}\" adicionado a tabela \"{:s}\"'.format(dCounteId, vLastTableId)
										else:
											lastTableId, lastTableNumber = getLastTablePartition(unitObj.tables, (dTableObj.partitionOf if re.search(r'_(\d+)$', dTableId) is not None else dTableId))
											if lastTableNumber > vLastTableNumber:
												tableObj = unitObj.getTable(lastTableId)
												if (tableObj.numberOfCounters + unitObj.numberOfAttributes) < 970:
													tableObj.addCounter(dCounteId, dCounteObj)
													print 'NewCounter: \"{:s}\" adicionado a tabela \"{:s}\"'.format(dCounteId, lastTableId)
												else:
													tableObj = table()
													lastTableNumber = '_' + str(lastTableNumber + 1)
													tableObj.create(re.sub(r'_(\d+)$', lastTableNumber, lastTableId), ossId, re.sub(r'_(\d+)$', lastTableNumber, dTableObj.sqlName), re.sub(r'_(\d+)$', lastTableNumber, dTableObj.udn))
													tableObj.addCounter(dCounteId, dCounteObj)
													unitObj.addTable(re.sub(r'_(\d+)$', lastTableNumber, lastTableId), tableObj)
													print 'NewCounter: \"{:s}\" adicionado a tabela \"{:s}\"'.format(dCounteId, re.sub(r'_(\d+)$', lastTableNumber, lastTableId))
											else:
												vLastTableObj.addCounter(dCounteId, dCounteObj)
												tableObj = table()
												tableObj.create(vLastTableId, ossId, dTableObj.sqlName, dTableObj.udn)
												tableObj.addCounter(dCounteId, dCounteObj)
												unitObj.addTable(vLastTableId, tableObj)
												unitObj.addTable(vLastTableId, tableObj)
												print 'NewCounter: \"{:s}\" adicionado a tabela \"{:s}\"'.format(dCounteId, vLastTableId)
									else:
										lastTableId, lastTableNumber = getLastTablePartition(unitObj.tables, (dTableObj.partitionOf if re.search(r'_(\d+)$', dTableId) is not None else dTableId))
										if lastTableNumber >= vLastTableNumber:
											tableObj = unitObj.getTable(lastTableId)
											if (tableObj.numberOfCounters + unitObj.numberOfAttributes) < 970:
												tableObj.addCounter(dCounteId, dCounteObj)
												print 'NewCounter: \"{:s}\" adicionado a tabela \"{:s}\"'.format(dCounteId, lastTableId)
											else:
												lastTableNumber = '_' + str(lastTableNumber + 1)
												lastTableId = re.sub(r'_(\d+)$', lastTableNumber, lastTableId)
												tableObj = table()
												tableObj.create(lastTableId, ossId, re.sub(r'_(\d+)$', lastTableNumber, dTableObj.sqlName), re.sub(r'_(\d+)$', lastTableNumber, dTableObj.udn))
												tableObj.addCounter(dCounteId, dCounteObj)
												unitObj.addTable(lastTableId, tableObj)
												print 'NewCounter: \"{:s}\" adicionado a tabela \"{:s}\"'.format(dCounteId, lastTableId)
										else:
											vLastTableNumber = '_' + str(vLastTableNumber + 1)
											lastTableId = re.sub(r'_(\d+)$', vLastTableNumber, lastTableId)
											if re.sub(r'_(\d+)$', vLastTableNumber, lastTableId) not in unitObj.tables.keys():
												tableObj = table()
												tableObj.create(lastTableId, ossId, re.sub(r'_(\d+)$', vLastTableNumber, dTableObj.sqlName), re.sub(r'_(\d+)$', vLastTableNumber, dTableObj.udn))
												tableObj.addCounter(dCounteId, dCounteObj)
												unitObj.addTable(lastTableId, tableObj)
												print 'NewCounter: \"{:s}\" adicionado a tabela \"{:s}\"'.format(dCounteId, lastTableId)
											else:
												tableObj = unitObj.getTable(lastTableId)
												tableObj.addCounter(dCounteId, dCounteObj)
												print 'NewCounter: \"{:s}\" adicionado a tabela \"{:s}\"'.format(dCounteId, lastTableId)
								except:
									tableObj = unitObj.getTable(dTableId)
									tableObj.addCounter(dCounteId, dCounteObj)


		else:
			print 'NewUnit: \"{:s}\"'.format(dUnitObj.ossId)
			data[ossId] = dUnitObj

	return data

# #
# Tries to get last table partition
# #
def getLastTablePartition(vTablesList, tableId):
	lastTableId = tableId
	lastTableNumber = 0
	for vTablesId in vTablesList.keys():
		if tableId in vTablesId:
			if re.search(r'^' + tableId + '_(\d+)$', vTablesId) is not None:
				tmp = int(re.sub(r'^.*._', '', vTablesId))
				if tmp > lastTableNumber:
					lastTableNumber = tmp
					lastTableId = vTablesId

	return lastTableId, lastTableNumber
