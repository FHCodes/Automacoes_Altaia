__doc__ = \
	__version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

# #
# Converts the typeCust in base of multiplicity
# #
def process(unitDict, config):

	for ossId in unitDict.keys():
		unitObj = unitDict[ossId]
		for elementId in unitObj.attributes.keys():
			elementObj = unitObj.attributes[elementId]
			if elementObj.multiplicity not in [None, '', '0', '1']:
				elementObj.bdtype = "VARCHAR2(1000)"
				elementObj.typeCust = 'STRING'

		for tableId in unitObj.tables.keys():
			tableObj = unitObj.tables[tableId]
			for elementId in tableObj.counters.keys():
				elementObj = tableObj.counters[elementId]
				if elementObj.multiplicity not in [None, '', '0', '1']:
					elementObj.bdtype = "VARCHAR2(1000)"
					elementObj.typeCust = 'STRING'
