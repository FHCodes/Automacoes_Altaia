__doc__ = \
	__version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

#from xml.etree.ElementTree import Element
import xml.etree.ElementTree as ET
import pkgutil
from collections import OrderedDict
import src.outputFormats.xml.operations
from lib.functions import writeStringToXML, writeOperationToXML, writeToXML

def process(data, config, parameters):
	rules = getOperations(config['outputFormat']['operationsCatalog'])
	config = config['collector']

	root = ET.Element('root', model=config['model'], ossversion=config['version'], vendor=config['vendor'])
	root.append(ET.Comment(config['version']))

	for ossId in sorted(data.keys()):
		unitObj = data[ossId]

		unit = ET.SubElement(root, 'unit')
		unit.set('id', unitObj.typeId.upper())

		if unitObj.operations != {}:
			operations = unitObj.operations
			if 'item' in operations.keys():
				for itemId in operations['item'].keys():
					try:
						itemXml = ET.SubElement(unit, 'item')
						itemXml.set('id', itemId.upper())
						for opXml in operations['item'][itemId]:
							itemXml.append(opXml)
					except:
						pass
			if 'unit' in operations.keys():
				for typeId in operations['unit'].keys():
					for opXml in operations['unit'][typeId]:
						try:
							if type(opXml) is ET.Element:
								unit.append(opXml)
							else:
								if typeId in rules['unit'].keys():
									rules['unit'][typeId]['module'].process(unit, unitObj, opXml)
						except Exception as e:
							print e
							pass
			pass
		if True:
			if 'unit' in rules.keys():
				for rule in rules['unit'].keys():
					for ruleConfig in rules['unit'][rule]['config']:
						rules['unit'][rule]['module'].process(unit, unitObj, ruleConfig)

			attributesDict = unitObj.attributes
			for attributeId in attributesDict.keys():
				attributeObj = attributesDict[attributeId]
				if attributeObj.multiplicity is not '' or 'item' in rules.keys():
					for rule in rules['item'].keys():
						for ruleConfig in rules['item'][rule]['config']:
							rules['item'][rule]['module'].process(unit, attributeObj, ruleConfig)

			tablesDict = unitObj.tables
			for tableId in tablesDict.keys():
				tableObj = tablesDict[tableId]
				countersDict = tableObj.counters
				for counterId in countersDict.keys():
					counterObj = countersDict[counterId]
					if counterObj.multiplicity is not '' and 'item' in rules.keys():
						for rule in rules['item'].keys():
							for ruleConfig in rules['item'][rule]['config']:
								rules['item'][rule]['module'].process(unit, counterObj, ruleConfig)

	#writeToXML(config['nameNomenclature'].replace('#', 'operations') + '.xml', ET.ElementTree(root))
	#writeStringToXML(config['nameNomenclature'].replace('#', 'operations') + '.xml', root)
	writeOperationToXML(config['nameNomenclature'].replace('#', 'operations') + '.xml', root)

def getOperations(config):
	outFormatList = OrderedDict()
	for key in config:
		outFormatList[key] = OrderedDict()
		for importer, packageName, xx in pkgutil.iter_modules(src.outputFormats.xml.operations.__path__):
			if packageName in config[key].keys():
				outFormatList[key][packageName] = dict()
				outFormatList[key][packageName]['module'] = importer.find_module(packageName).load_module(packageName)
				outFormatList[key][packageName]['config'] = config[key][packageName]
	return outFormatList