from lxml.etree import Element
import lxml.etree as ET
import re
from lib.functions import xmlReader
from lib.functions import writeStringToXML


def convertByExport(catalogPath, exportDataPath):
	exportedData = exporterReader(exportDataPath)

	root = xmlReader(catalogPath)
	for table in root.findall('table'):
		tableName = table.get('tableName').upper()
		if tableName in exportedData.keys():
			if 'udn' in exportedData[tableName].keys():
				table.attrib['udn'] = exportedData[tableName]['udn']
			items = exportedData[tableName]['items']
			for column in table.findall('column'):
				bdcolname = column.get('bdcolname').upper()
				if bdcolname in items.keys():
					column.attrib['udn'] = items[bdcolname]

	writeStringToXML(re.search(r'.*\\([^\\]*?)$|.*/([^/]*?)$', catalogPath).group(1), root)


def exporterReader(path):

	exportData = ET.parse(path)

	data = dict()

	for table in exportData.xpath("//*[local-name() = $name]", name = 'table'):
		tableName = table.get('name').split('.')[1]
		if tableName not in data.keys():
			data[tableName] = dict()
			data[tableName]['items'] = dict()
			if 'inventoryTypeName' in table.attrib.keys():
				data[tableName]['udn'] = table.get('inventoryTypeName')
		for item in table.iter():
			if 'inventoryName' in item.attrib.keys():
				data[tableName]['items'][item.get('name')] = item.get('inventoryName')
	return data
