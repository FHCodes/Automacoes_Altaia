__doc__ = \
	__version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

from xml.etree.ElementTree import Element
import xml.etree.ElementTree as ET
from lib.functions import xmlReader, writeToXML
import pkgutil
import src.merge.xml.operations
from lib.Logger import Logger

# #
# Merges two XML operations catalogs into one, being the baseCatalogPath the base for the output
# #
def process(vendor, baseCatalogPath, newCatalogPath, numenclature, config):
	logger = Logger('operationsMerge').get()

	baseCatalog = xmlReader(baseCatalogPath.replace('#', 'operations'))
	newCatalog = xmlReader(newCatalogPath.replace('#', 'operations'))

	logger.debug('#################################### Operation Merging Info ########################################')
	logger.debug('## Vendor: {:34s}                                                     ##'.format(vendor))
	logger.debug('## Base: {:40s}   New: {:40s} ##'.format(baseCatalog.get('ossversion'), newCatalog.get('ossversion')))
	logger.debug('## Output File:  {:80} ##'.format(numenclature.replace('#', 'operations')))
	logger.debug('################################### Start Operation Merging ########################################')

	data = dict()
	comment = list()
	baseCatalog.attrib['ossversion'] = str(baseCatalog.get('ossversion')) + '/' + str(newCatalog.get('ossversion'))

	for newIndexesXML in newCatalog.findall('indexes'):
		newIndexes = True
		for indexesXML in baseCatalog.findall('indexes'):
			newIndexes = False
			for newIndexXML in newIndexesXML.findall('index'):
				newIndex = True
				for indexXML in indexesXML.findall('index'):
					if len(indexXML.findall('key')) == len(newIndexXML.findall('key')):
						allEqual = True
						for newKeyXML in newIndexXML.findall('key'):
							notFound = True
							for keyXML in indexXML.findall('key'):
								if keyXML.get('name') == newKeyXML.get('name'):
									notFound = False
							if notFound:
								allEqual = False
						if allEqual:
							newIndex = False
				if newIndex:
					indexesXML.append(newIndexXML)
		if newIndexes:
			baseCatalog.insert(0, newIndexesXML)



	operations = getOperations()
	for unit in baseCatalog.findall('unit'):
		unitId = unit.get('id')
		if unitId is None:
			if ET.tostring(unit).upper() not in comment:
				comment.append(ET.tostring(unit).upper())
		else:
			unitId = unitId.upper()
			if unitId not in data.keys():
				data[unitId] = dict()
				data[unitId]['unit'] = unit
				data[unitId]['operation'] = dict()
				data[unitId]['item'] = dict()
				data[unitId]['comments'] = list()

				for baseElement in unit:
					if baseElement.tag == 'item':
						baseElementId = baseElement.get('id').upper()
						data[unitId]['item'][baseElementId] = dict()
						data[unitId]['item'][baseElementId]['operation'] = list()
						for op in baseElement.findall('operation'):
							#if op.get('type') not in data[unitId]['item'][baseElementId]:
							#	data[unitId]['item'][baseElementId][op.get('type')] = list()
							data[unitId]['item'][baseElementId]['element'] = baseElement
							data[unitId]['item'][baseElementId]['operation'].append(op.get('type'))
					elif baseElement.tag == 'operation':
						#if baseElement.get('type') not in data[unitId]['operation'].keys():
						#	data[unitId]['operation'][baseElement.get('type')] = list()
						data[unitId]['operation'][baseElement.get('type')] = unit
			else:
				logger.warning('Duplicated unit id for \"' + unitId + '\"')

	for newUnit in newCatalog.findall('unit'):
		newUnitId = newUnit.get('id')
		#print newUnitId
		operationsOfUnitProcessed = list()
		if newUnitId is None:
			if ET.tostring(newUnit).upper() not in comment:
				baseCatalog.append(newUnit)
		else:
			newUnitId = newUnitId.upper()
			if newUnitId in data.keys():
				unitToAppend = data[newUnitId]['unit']
				for newElement in newUnit:
					operationsOfItemProcessed = list()
					newElementTag = newElement.tag
					if newElementTag is None:
						if ET.tostring(newElement).upper() not in data[newUnitId]['comments']:
							unitToAppend.append(newElement)
					else:
						if newElementTag == 'operation':
							#operation
							newElementType = newElement.get('type')
							if newElementType in data[newUnitId]['operation'].keys() and newElementType not in operationsOfUnitProcessed:
								if newElementType not in operations.keys():
									logger.error('Operation type \"' + newElementType + '\" from unit \"' + newUnitId + '\" was not found on defined operations')
									continue
								operations[newElementType].process(data[newUnitId]['operation'][newElementType], newUnit)
								operationsOfUnitProcessed.append(newElementType)
							elif newElementType not in operationsOfUnitProcessed:
								unitToAppend.insert(len(baseCatalog.keys()), newElement)
						elif newElementTag == 'item':
							#Items
							newElementId = newElement.get('id').upper()
							if newElementId in data[newUnitId]['item'].keys():
								for newElementOp in newElement.findall('operation'):
									newElementOpType = newElementOp.get('type')
									if newElementOpType in data[newUnitId]['item'][newElementId]['operation'] and newElementOpType not in operationsOfItemProcessed:
										if newElementOpType not in operations.keys():
											logger.error('from item \"' + newElementId + '\" in unit \"' + newUnitId + '\" was not found on defined operations')
											logger.error('Operation type \"' + newElementOpType + '\" from item \"' + newElementId + '\" in unit \"' + newUnitId + '\" was not found on defined operations')
											continue
										operations[newElementOpType].process(data[newUnitId]['item'][newElementId]['element'], newElement)
										operationsOfItemProcessed.append(newElementOpType)
									elif newElementOpType not in operationsOfItemProcessed:
										data[newUnitId]['item'][newElementId]['element'].append(newElementOp)
							else:
								unitToAppend.insert(0, newElement)
			else:
				baseCatalog.insert(len(baseCatalog.keys()), newUnit)


	writeToXML(numenclature.replace('#', 'operations'), ET.ElementTree(baseCatalog))
	#writeOperationToXML(numenclature.replace('#', 'operations'), baseCatalog)
	logger.debug('#################################### End Operation Merging #########################################')

# #
# Loads all operations that are configurations in the dir operations
# #
def getOperations():
	operations = dict()
	for importer, packageName, _ in pkgutil.iter_modules(src.merge.xml.operations.__path__):
		operations[packageName] = importer.find_module(packageName).load_module(packageName)
	return operations
