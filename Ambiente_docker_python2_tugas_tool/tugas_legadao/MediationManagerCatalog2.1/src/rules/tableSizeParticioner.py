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
				newCountersList = list()
				tempId = re.sub(r'_(\d+)', '', tableId)
				for newCounterId in tablesDict.keys():
					if re.search(tempId + '_(\d+)$', newCounterId) is not None:
						newCountersList.append(newCounterId)

				newCounterObj = None
				if len(newCountersList) > 0:
					newCountersList = sorted(newCountersList)
					if newCountersList[-1] != tableId and (tablesDict[newCountersList[-1]].numberOfCounters + unitObj.numberOfAttributes) < 970:
						newCounterObj = tablesDict[newCountersList[-1]]
					else:
						try:
							partitionNumber = int(newCountersList[-1].split('_')[-1]) + 1
						except Exception as ex:
							logger.warning('{:s} In table "{:s}" Exception: {:s})'.format('rule.tableSizeParticioner',tableId, ex.message))
							partitionNumber = 1
						newCounterObj = table()
						newCounterObj.create(tempId + '_' + str(partitionNumber), ossId, re.sub(r'_(\d+)', '', tableObj.sqlName) + '_' + str(partitionNumber), re.sub(r'_(\d+)', '', tableObj.udn) + '_' + str(partitionNumber))
						newCounterObj.partitionOf = tempId
						if newCounterObj.typeId in unitObj.tables.keys():
							logger.warning(' * Criacao de particao correu mal * ')
						unitObj.addTable(tempId + '_' + str(partitionNumber), newCounterObj)
				else:
					newCounterObj = table()
					newCounterObj.create(tempId + '_1', ossId, tableObj.sqlName + '_1', tableObj.udn + '_1')
					newCounterObj.partitionOf = tempId
					if newCounterObj.typeId in unitObj.tables.keys():
						logger.warning(' * Criacao de particao correu mal * ')
						continue
					unitObj.addTable(tempId + '_1', newCounterObj)

				if newCounterObj == None:
					logger.warning(' * Criacao de particao correu mal * ')
					continue

				counterId = tableObj.counters.keys()[-1]
				counterObj = tableObj.getCounter(counterId)
				newCounterObj.addCounter(counterId, counterObj)
				tableObj.removeCounter(counterId)

			partitionNumber = len(unitObj.tables) - 1
			for pdfObj in tablePDFList:
				pdfOnlyConvert = True
				particionerConvert = True
				partitionNumber += 1
				newCounterObj = table()
				newCounterObj.create(tableId + '_' + str(partitionNumber), ossId, tableObj.sqlName + '_' + str(partitionNumber), tableObj.udn + '_' + pdfObj.typeId)
				newCounterObj.partitionOf = tableId
				newCounterObj.pdfOnly = 'True'
				unitObj.addTable(tableId + '_' + str(partitionNumber), newCounterObj)
				for i in range(0, int(pdfObj.multiplicity)):
					counterObj = column()
					counterObj.create(pdfObj.typeId + 'Sub' + str(i), pdfObj.name + 'Sub' + str(i), pdfObj.udn + 'Sub' + str(i), pdfObj.sqlName + 'Sub' + str(i), pdfObj.desc + '[' + str(i) + ']', 'MT', 'NUMBER', (pdfObj.typeCust if pdfObj.typeCust not in ['PDF', 'DDM'] else 'INTEGER'), (pdfObj.typeVendor if pdfObj.typeVendor not in ['PDF', 'DDM'] else 'INTEGER'),(pdfObj.unitVendor if pdfObj.unitVendor not in ['PDF', 'DDM'] else ''), 0)
					newCounterObj.addCounter(counterObj.typeId, counterObj)

				if pdfObj.typeVendor not in ['PDF', 'DDM']:
					pdfObj.typeVendor = 'PDF'
					pdfObj.unitVendor = 'PDF'
				pdfObj.bdtype = 'VARCHAR2(600)'
				pdfObj.typeCust = 'STRING'
				newCounterObj.addCounter(pdfObj.typeId, pdfObj)

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
