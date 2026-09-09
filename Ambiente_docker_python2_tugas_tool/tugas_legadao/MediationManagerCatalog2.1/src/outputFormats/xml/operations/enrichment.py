__doc__ = \
	__version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

from xml.etree.ElementTree import Element
import xml.etree.ElementTree as ET

def process(element, unitObj, config):
	"""
	(Atencao: Funcionamento de enrichment da NOKIA APENAS)


	<operation complexoperation="true" type="enrichment">
		<scope>NSN_NETACT_BSC</scope>
		<corrKey>DISTNAME</corrKey>
		<newField>BSC_NAME</newField>
		<newField>BTS_NAME</newField>
		<newField>CELLID</newField>
		<newField>CELLNAME</newField>
	</operation>

	Command:
	"enrichment":
	[
		{
			"scope": "NSN_NETACT_BSC",
			"corrKey": [("DISTNAME", "")] # Para existir em todos ''
			"newField": [("BSC_NAME", "BSC"), ("BTS_NAME", "BCF"), ("CELLID", "BTS"), ("CELLNAME", "BTS")]
		}
	]
	"""
	operationXML = ET.SubElement(element, 'operation')
	operationXML.set('complexoperation', "true")
	operationXML.set('type', 'enrichment')
	scopeXML = ET.SubElement(operationXML, 'scope')
	scopeXML.text = config['scope']

	for corrDict in config['corrKey']:
		corrKey = corrDict.keys()[0]
		depExists = False
		for dependencie in corrDict[corrKey]:
			if dependencie == '':
				depExists = True
			elif dependencie in [x.upper() for x in unitObj.attributes.keys()]:
				depExists = True
			else:
				for tableId in unitObj.tables.keys():
					tableObj = unitObj.getTable(tableId)
					if dependencie in [x.upper() for x in tableObj.counters.keys()]:
						depExists = True

		if depExists:
			corrKeyXML = ET.SubElement(operationXML, 'corrKey')
			corrKeyXML.text = corrKey

	for newFieldDict in config['newField']:
		newField = newFieldDict.keys()[0]
		depExists = False
		for dependencie in newFieldDict[newField]:
			if dependencie in [x.upper() for x in unitObj.attributes.keys()]:
				depExists = True
			else:
				for tableId in unitObj.tables.keys():
					tableObj = unitObj.getTable(tableId)
					if dependencie in [x.upper() for x in tableObj.counters.keys()]:
						depExists = True

			if depExists:
				newFieldXML = ET.SubElement(operationXML, 'newField')
				newFieldXML.text = newField
				break

