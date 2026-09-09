__doc__ = \
	__version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

import xml.etree.ElementTree as ET
from lib.functions import writeStringToXML, writeToXML

def process(data, config, parameters):

	config = config['collector']
	root = ET.Element('root', model=config['model'], ossversion=config['version'], vendor=config['vendor'])
	root.append(ET.Comment(config['version']))

	for ossId in sorted(data.keys()):
		unitItemList = list()
		unitObj = data[ossId]
		appendToRoot = False

		for tableId in unitObj.tables:
			tableObj = unitObj.tables[tableId]
			alterData = False
			if tableId != ossId:
				alterData = True

			unit = ET.Element('unit')
			unit.set('id', tableId)
			unit.set('ossId', tableId)
			unit.set('name', tableId)
			unit.set('desc', unitObj.desc)
			unit.set('measuredobjects', unitObj.measuredObject)
			unit.set('tech', (config['tech'] if unitObj.tech == '' else unitObj.tech))
			extraDict = unitObj.getExtraCatalog('oss')
			for attr in extraDict.keys():
				unit.set(attr, extraDict[attr].value)

			if unitObj.isDummy:
				root.append(unit)
				continue

			attributeDict = unitObj.attributes
			for attributeId in attributeDict.keys():
				if attributeId not in unitItemList:
					unitItemList.append(attributeId)
					attributeObj = attributeDict[attributeId]
					column = ET.SubElement(unit, 'item')
					column.set('id', attributeObj.typeId.upper())
					column.set('name', attributeObj.name.upper())
					column.set('desc', attributeObj.desc)
					column.set('typeCust', attributeObj.typeCust)
					column.set('typeVendor', attributeObj.typeVendor)
					column.set('unitVendor', attributeObj.unitVendor)
					column.set('seqlength', 'Single')
					if attributeObj.version != '':
						column.set('v', attributeObj.version)
					elif '/' in config['version']:
						column.set('v', config['version'])
					else:
						column.set('v', config['version'] + '/' + config['version'])
					extraDict = attributeObj.getExtraCatalog('oss')
					for attr in extraDict.keys():
						column.set(attr, extraDict[attr].value)

			tableDict = unitObj.tables
			for tableId in tableDict.keys():
				tableObj = tableDict[tableId]
				if tableObj.isStruct == False or config['vendor'] != 'ERICSSON':
					appendToRoot = True
					countersDict = tableObj.counters
					for counterId in countersDict.keys():
						if counterId not in unitItemList:
							unitItemList.append(counterId)
							counterObj = countersDict[counterId]
							column = ET.SubElement(unit, 'item')
							column.set('id', counterObj.typeId.upper())
							column.set('name', counterObj.name)
							column.set('desc', counterObj.desc)
							column.set('typeCust', counterObj.typeCust)
							column.set('typeVendor', counterObj.typeVendor)
							column.set('unitVendor', counterObj.unitVendor)
							if counterObj.multiplicity in ['', 0]:
								column.set('seqlength', 'Single')
							else:
								column.set('seqlength', '[{:s}]'.format(counterObj.multiplicity))

							if counterObj.version != '':
								column.set('v', counterObj.version)
							elif '/' in config['version']:
								column.set('v', config['version'])
							else:
								column.set('v', config['version'] + '/' + config['version'])
							extraDict = counterObj.getExtraCatalog('oss')
							for attr in extraDict.keys():
								column.set(attr, extraDict[attr].value)

		if appendToRoot:
			root.append(unit)

	#writeToXML(config['nameNomenclature'].replace('#', 'oss') + '.xml', ET.ElementTree(root))
	writeStringToXML(config['nameNomenclature'].replace('#', 'oss') + '.xml', root)
