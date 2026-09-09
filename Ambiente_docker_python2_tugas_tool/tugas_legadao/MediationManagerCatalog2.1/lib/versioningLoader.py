__doc__ = \
	__version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

import os, re, json
import copy
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

	elif shelfPath.endswith('.xml'):
		clientRoot = xmlReader(shelfPath.replace('#', 'client'))
		ossRoot = xmlReader(shelfPath.replace('#', 'oss'))
		operationsRoot = xmlReader(shelfPath.replace('#', 'operations'))

		data, matchId = getCientStruct(clientRoot, data)
		data = getOssStruct(ossRoot, data)
		data = getOperationsStruct(operationsRoot, data, matchId)
	elif shelfPath.endswith('.json'):
		getLoadingCatalog(shelfPath)
	else:
		path = '../../../../trunk/conf/catalogos/collectorProcess/Catalogs/{:s}/Product_Packs_Shelf/{:s}/'.format(
			vendor, collectorName)
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
		ossId = tableXml.get('ossId').upper()
		if ossId not in data.keys():
			unitObj = unit()
			unitObj.create(ossId, tableXml.get('id').upper(), '', '', '')
			unitObj.tech = tableXml.get('tech')
			unitObj.size = 1
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

			tableObj.update('ACTIVE', tableXml.get('active'))

			mtc = re.match(ossId + '_(?P<number>\d+)$', tableObj.sqlName)
			if mtc is not None:
				tableObj.partitionOf = ossId
				if int(mtc.group('number')) > unitObj.size:
					unitObj.size = int(mtc.group('number'))
			unitObj.addTable(tableId.upper(), tableObj)

		for columnXml in tableXml.findall('column'):
			columnId = columnXml.get('id').upper()
			if columnId in tableObj.counters.keys():
				logger.warning(
					' * [versioningLoader] Duplicated column id \"{:s}\" was found on table \"{:s}\" * '.format(
						columnId, tableId))
				continue
			columnObj = column()
			columnObj.create(columnId, '', columnXml.get('udn'), columnXml.get('bdcolname').upper(), '', columnXml.get('dbn0type'), columnXml.get('bdtype'), '', '', '', 0)
			if columnObj.dbn0type in ['PK', 'ID']:
				unitObj.addAttribute(columnId, copy.deepcopy(columnObj))
			else:
				tableObj.addCounter(columnId, columnObj)
	return data, matchId


# #
# Reads and converts oss catalog data to program acceptable data format
# #
def getOssStruct(root, data):
	logger = Logger('processLogger').get()
	# measuredobjects
	for unitXml in root.findall('unit'):
		ossId = unitXml.get('ossId').upper()
		if ossId not in data.keys():
			logger.error(' * [versioningLoader] ossId \"{:s}\" was not found in client catalog. * '.format(ossId))
		else:
			unitObj = data[ossId]
			unitObj.measuredObject = unitXml.get('measuredobjects')
			unitObj.name = unitXml.get('name')
			unitObj.desc = unitXml.get('desc')

			tableList = unitObj.tables
			for itemXml in unitXml.findall('item'):
				itemId = itemXml.get('id').upper()
				if itemId in unitObj.attributes.keys():
					counterObj = unitObj.attributes[itemId]
					counterObj.name = itemXml.get('name')
					counterObj.desc = itemXml.get('desc')
					counterObj.typeCust = itemXml.get('typeCust')
					counterObj.typeVendor = itemXml.get('typeVendor')
					counterObj.unitVendor = itemXml.get('unitVendor')
					counterObj.version = itemXml.get('v')
					if 'seqlength' in itemXml.attrib.keys():
						counterObj.multiplicity = itemXml.get('seqlength')

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
						counterObj.version = itemXml.get('v')
						if 'seqlength' in itemXml.attrib.keys():
							if '[' in itemXml.get('seqlength'):
								counterObj.multiplicity = re.sub('[\]\[.]', '', itemXml.get('seqlength'))
							else:
								counterObj.multiplicity = '0'
						break

				if isMissing:
					logger.warning(
						' * [versioningLoader] itemId \"{:s}\" from ossId \"{:s}\" was not found in client catalog. * '.format(
							itemId, ossId))
	return data


# #
# Reads and converts operations catalog data to program acceptable data format
# #
def getOperationsStruct(root, data, matchId):
	logger = Logger('processLogger').get()

	for unitXml in root.findall('unit'):
		unitId = unitXml.get('id').upper()

		if unitId in matchId.keys():
			ossId = matchId[unitId]
			unitObj = data[ossId]
			for opXml in unitXml.findall('operation'):
				unitObj.addOperation('unit', unitId, opXml)
			for itemXml in unitXml.findall('item'):
				itemId = itemXml.get('id').upper()
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
		ossId = unitDict['id']
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
		tableObj.update('PARTITIONOF', unitDict['partitionOf'])

		for itemDict in unitDict['measItems']:
			columnObj = column()
			columnObj.create(itemDict['id'], itemDict['name'], itemDict['udn'], itemDict['columnName'], itemDict['description'], itemDict['measItemType'], itemDict['type'], itemDict['typeCust'], itemDict['typeVendor'], itemDict['unitVendor'], 0)
			#if itemDict['measItemType'] in ['PK', 'ID']:
			#	unitObj.addAttribute(itemDict['id'], columnObj)
			#	continue
			#elif itemDict['measItemType'] in ['MT', 'CM']:
			tableObj.addCounter(itemDict['id'], columnObj)

		if len(tableObj.counters.keys()) == 0:
			tableObj.setDummy()

	return data


# #
# Converts data/catalog to be in coherence with "historic" (previous versions)
# #
def convertData(data, vendor, collectorName, shelfPath):
	versionData = getVersioningHistoric(vendor, collectorName, shelfPath)

	for ossId in data.keys():
		if ossId in versionData.keys():
			unitObj = data[ossId]
			vsUnitObj = versionData[ossId]

			# comparar e actualizar UNIT
			unitObj.size = vsUnitObj.size
			# print '{0}: {1}'.format(ossId, unitObj.size)
			if vsUnitObj.name not in ['', None]:
				unitObj.name = vsUnitObj.name
				unitObj.tech = vsUnitObj.tech

			for attributeId in unitObj.attributes.keys():
				if attributeId in vsUnitObj.attributes.keys():
					attributeObj = unitObj.attributes[attributeId]
					vsAttributeObj = vsUnitObj.attributes[attributeId]

				# comparar e actualizar ATTRIBUTES
					attributeObj.name = vsAttributeObj.name
					attributeObj.sqlName = vsAttributeObj.sqlName
					attributeObj.udn = vsAttributeObj.udn
					attributeObj.dbn0type = vsAttributeObj.dbn0type
					attributeObj.bdtype = vsAttributeObj.bdtype

			for tableId in unitObj.tables.keys():
				tableObj = unitObj.tables[tableId]
				if tableId in vsUnitObj.tables.keys():
					vsTableObj = vsUnitObj.tables[tableId]
					listOfTables = sorted(getNewCounters(vsUnitObj.tables.keys(), ossId.upper()))
					# comparar e actualizar TABLE
					if vsTableObj.active not in ['', None]:
						tableObj.active = vsTableObj.active
					if vsTableObj.name not in ['', None]:
						tableObj.name = vsTableObj.name
					if vsTableObj.sqlName not in ['', None]:
						tableObj.sqlName = vsTableObj.sqlName
					if vsTableObj.udn not in ['', None]:
						tableObj.udn = vsTableObj.udn
					tableObj.tech = vsTableObj.tech
					listToRemove = list()
					for columnId in tableObj.counters.keys():
						columnObj = tableObj.counters[columnId]
						if columnId in vsTableObj.counters.keys():
							vsColumnObj = vsTableObj.counters[columnId]
							# comparar e actualizar COLUMN
							if vsColumnObj.name not in ['', None]:
								columnObj.name = vsColumnObj.name
							if vsColumnObj.sqlName not in ['', None]:
								columnObj.sqlName = vsColumnObj.sqlName
							if vsColumnObj.udn not in ['', None]:
								columnObj.udn = vsColumnObj.udn
							if vsColumnObj.dbn0type not in ['', None]:
								columnObj.dbn0type = vsColumnObj.dbn0type
							if vsColumnObj.bdtype not in ['', None]:
								columnObj.bdtype = vsColumnObj.bdtype
						else:
							counterFound = False
							for vsTableId in listOfTables:
								tmpTableObj = vsUnitObj.tables[vsTableId]
								if columnId in tmpTableObj.counters.keys():
									tmpColumnObj = tmpTableObj.counters[columnId]
									if vsTableId not in unitObj.tables.keys():
										newTableObj = table()
										newTableObj.create(vsTableId, ossId, tmpTableObj.get('SQLNAME'), tmpTableObj.get('UDN'))
										data[ossId].addTable(vsTableId, newTableObj)
									else:
										newTableObj = unitObj.tables[vsTableId]

									columnObj = copy.deepcopy(columnObj)
									newTableObj.addCounter(columnId, columnObj)
									if tmpColumnObj.name not in ['', None]:
										columnObj.name = tmpColumnObj.name
									if tmpColumnObj.sqlName not in ['', None]:
										columnObj.sqlName = tmpColumnObj.sqlName
									if tmpColumnObj.udn not in ['', None]:
										columnObj.udn = tmpColumnObj.udn
									if tmpColumnObj.dbn0type not in ['', None]:
										columnObj.dbn0type = tmpColumnObj.dbn0type
									if tmpColumnObj.bdtype not in ['', None]:
										columnObj.bdtype = tmpColumnObj.bdtype
									listToRemove.append(columnId)
									counterFound = True
									break

							if not counterFound and len(listOfTables) != 0:
								if listOfTables[-1] not in unitObj.tables.keys():
									tmpTableObj = vsUnitObj.tables[listOfTables[-1]]

									newTableObj = table()
									newTableObj.create(listOfTables[-1], ossId, tmpTableObj.get('SQLNAME'), tmpTableObj.get('UDN'))
									data[ossId].addTable(listOfTables[-1], newTableObj)
								else:
									if unitObj.tables[listOfTables[-1]].numberOfCounters < 970:
										newTableObj = unitObj.tables[listOfTables[-1]]
									else:
										unitObj.size = unitObj.size + 1
										if re.search('^' + ossId.upper() + '_(\d+)$', tableId) != None:
											newTableId = re.sub('_(\d+)$', unitObj.size, tableId)
										else:
											newTableId = tableId + '_newCounters'

										if re.search('_(\d+)$', tableObj.get('SQLNAME')):
											newTableName = re.sub('_(\d+)$', str(unitObj.size), tableObj.get('SQLNAME'))
										else:
											newTableName = tableObj.get('SQLNAME') + '_' + str(unitObj.size)
										newTableObj = table()
										newTableObj.create(newTableId.upper(), ossId, newTableName, newTableId)
										data[ossId].addTable(newTableId.upper(), newTableObj)
										vsUnitObj.addTable(newTableId.upper(), copy.deepcopy(newTableObj))
										for attributeId in unitObj.attributes.keys():
											newTableObj.addCounter(attributeId, copy.deepcopy(unitObj.attributes[attributeId]))

								listToRemove.append(columnId)
								columnObj = copy.deepcopy(columnObj)
								newTableObj.addCounter(columnId, columnObj)

					for cId in listToRemove:
						tableObj.removeCounter(cId)
				else:
					if re.search('^' + ossId.upper() + '_(\d+)$', tableObj.sqlName) != None:
						unitObj.size = unitObj.size + 1
						tableObj.sqlName = '{0}_{1}'.format(ossId, str(unitObj.size))

		#data[ossId].clearAttributes()
	return data


# #
# Gets list of all newCounters from one table
# #
def getNewCounters(tableList, tableId):
	listOfTables = list()

	for newTableId in tableList:
		if re.search(r'^' + tableId + '_NEWCOUNTERS', newTableId) != None:
			listOfTables.append(newTableId)

	return listOfTables


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
