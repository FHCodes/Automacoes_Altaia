__doc__ = \
	__version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

from lib.objects.column import column
from lib.objects.table import table
from lib.objects.unit import unit
from lib.Logger import Logger
import re

# #
# Validates the tables sizes and creates partitions if needed
# #
def process(unitDict, config):
	logger = Logger('processLogger').get()
	pdfOnlyConvert = False
	particionerConvert = False

	for ossId in unitDict.keys():
		unitObj = unitDict[ossId]
		tablesDict = unitObj.tables
		for tableId in tablesDict.keys():
			tableObj = tablesDict[tableId]
			tablePDFList = list()
			for counterId in tableObj.counters.keys():
				counterObj = tableObj.getCounter(counterId)
				if counterObj.multiplicity not in ['', 0]:
					tablePDFList.append(counterObj)
					tableObj.removeCounter(counterId)

			while (tableObj.numberOfCounters + unitObj.numberOfAttributes) > 970:
				particionerConvert = True
				newTableList = list()

				#tempId = re.sub(r'_(\d+)', '', tableId)
				for newTableId in tablesDict.keys():
					if re.search(tableId + '_newCounters(_*)(\d*)$', newTableId) is not None:
						newTableList.append(newTableId)

				newTableObj = None
				if len(newTableList) > 0:
					newTableList = sorted(newTableList)
					if newTableList[-1] != tableId and (tablesDict[newTableList[-1]].numberOfCounters + unitObj.numberOfAttributes) < 970:
						newTableObj = tablesDict[newTableList[-1]]
					else:
						partitionFind = re.match(tableId + '_newCounters_(?P<partitionNumber>(\d+))$')
						if partitionFind != None:
							partitionNumber = int(partitionFind.group('partitionNumber')) + 1
							newTableId = re.sub('_(\d*)$', '_' + str(partitionNumber), tableId)
						else:
							newTableId = tableId + '_1'

						newTableObj = table()
						newTableObj.create(newTableId, newTableId, re.sub(r'_(\d+)', '', tableObj.sqlName) + '_' + str(unitObj.size), '{0}_{1}'.format(tableObj.udn, 'newCounters'))
						unitObj.size += 1
						newTableObj.partitionOf = tableId
						if newTableObj.typeId in unitObj.tables.keys():
							logger.warning(' * Criacao de particao correu mal * ')
							continue
						unitObj.addTable(newTableId, newTableObj)

				else:
					newTableObj = table()
					newTableId = tableId + '_newCounters'
					newTableObj.create(newTableId, newTableId, tableObj.sqlName+'_0', tableObj.udn + '_newCounters')
					newTableObj.partitionOf = ossId
					if newTableObj.typeId in unitObj.tables.keys():
						logger.warning(' * Criacao de particao correu mal * ')
						continue
					unitObj.addTable(newTableId, newTableObj)

				if newTableObj == None:
					logger.warning(' * Criacao de particao correu mal * ')
					continue

				counterId = tableObj.counters.keys()[-1]
				counterObj = tableObj.getCounter(counterId)
				newTableObj.addCounter(counterId, counterObj)
				tableObj.removeCounter(counterId)

			partitionNumber = len(unitObj.tables) - 1
			for pdfObj in tablePDFList:
				pdfOnlyConvert = True
				particionerConvert = True
				newCounterTableObj = table()
				newTableId = tableId + '_' + pdfObj.typeId
				newCounterTableObj.create(newTableId, newTableId, tableObj.sqlName + '_' + str(unitObj.size), '{0}_{1}'.format(tableObj.get('UDN'), pdfObj.udn))
				unitObj.size += 1
				newCounterTableObj.partitionOf = ossId
				if 'Compressed: True' in pdfObj.desc:
					newCounterTableObj.pdfOnly = 'True'
				else:
					newCounterTableObj.pdfOnly = 'False'
				unitObj.addTable(newTableId, newCounterTableObj)
				for i in range(0, int(pdfObj.multiplicity)):
					counterObj = column()
					counterObj.create(pdfObj.typeId + 'Sub' + str(i), pdfObj.name + 'Sub' + str(i), pdfObj.udn + 'Sub' + str(i), pdfObj.sqlName + 'Sub' + str(i), '[' + str(i) + ']', 'MT', 'NUMBER', (pdfObj.typeCust if pdfObj.typeCust not in ['PDF', 'DDM'] else 'INTEGER'), (pdfObj.typeVendor if pdfObj.typeVendor not in ['PDF', 'DDM'] else 'INTEGER'),(pdfObj.unitVendor if pdfObj.unitVendor not in ['PDF', 'DDM'] else ''), 0)
					newCounterTableObj.addCounter(counterObj.typeId, counterObj)

				if pdfObj.typeVendor not in ['PDF', 'DDM']:
					pdfObj.typeVendor = 'PDF'
					pdfObj.unitVendor = 'PDF'
				pdfObj.bdtype = 'VARCHAR2(600)'
				pdfObj.typeCust = 'STRING'
				pdfObj.dbn0type = 'ID'
				newCounterTableObj.addCounter(pdfObj.typeId, pdfObj)

	if pdfOnlyConvert or particionerConvert:
		for ossId in unitDict.keys():
			unitObj = unitDict[ossId]
			tablesDict = unitObj.tables
			for tableId in tablesDict.keys():
				tableObj = tablesDict[tableId]
				if tableObj.pdfOnly == '' and pdfOnlyConvert:
					tableObj.pdfOnly = 'False'
				if tableObj.partitionOf == '' and particionerConvert:
					tableObj.partitionOf = unitObj.typeId
