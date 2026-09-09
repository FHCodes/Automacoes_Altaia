__doc__ = \
	__version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

from lib.objects.column import column

# #
# If in all patterns exists the level creates it, from high hierarchy level to low
# #
def process(unitDict, config):

	for ossId in unitDict.keys():
		unitObj = unitDict[ossId]

		for attrId in unitObj.attributes.keys():
			if attrId in ['NRBTS', 'NRCELL']:
				enrich5G(unitObj, attrId)
			elif attrId in ['MRBTS', 'LNBTS', 'LNCEL']:
				enrich4G(unitObj, attrId)
			elif attrId in ['RNC', 'WBTS', 'WCEL']:
				enrich3G(unitObj, attrId)
			elif attrId in ['BSC', 'BTS', 'BCF']:
				enrich2G(unitObj, attrId)

def enrich5G(unitObj, attrId):
	if attrId == 'NRBTS':
		if 'MRBTS_NAME' not in unitObj.attributes.keys():
			columnObj = column()
			columnObj.create('MRBTS_NAME', 'MRBTS_NAME', 'MRBTS_NAME', 'MRBTS_NAME', 'MRBTS_NAME', 'ENRICH',
			                 'VARCHAR2(255)', 'STRING', 'STRING', 'N/A', '')
			unitObj.addAttribute('MRBTS_NAME', columnObj)

		if 'NRBTS_NAME' not in unitObj.attributes.keys():
			columnObj = column()
			columnObj.create('NRBTS_NAME', 'NRBTS_NAME', 'NRBTS_NAME', 'NRBTS_NAME', 'NRBTS_NAME', 'ENRICH',
			                 'VARCHAR2(255)', 'STRING', 'STRING', 'N/A', '')
			unitObj.addAttribute('NRBTS_NAME', columnObj)

		return

	if attrId == 'NRCELL':
		if 'MRBTS_NAME' not in unitObj.attributes.keys():
			columnObj = column()
			columnObj.create('MRBTS_NAME', 'MRBTS_NAME', 'MRBTS_NAME', 'MRBTS_NAME', 'MRBTS_NAME', 'ENRICH',
			                 'VARCHAR2(255)', 'STRING', 'STRING', 'N/A', '')
			unitObj.addAttribute('MRBTS_NAME', columnObj)

		if 'NRBTS_NAME' not in unitObj.attributes.keys():
			columnObj = column()
			columnObj.create('NRBTS_NAME', 'NRBTS_NAME', 'NRBTS_NAME', 'NRBTS_NAME', 'NRBTS_NAME', 'ENRICH',
			                 'VARCHAR2(255)', 'STRING', 'STRING', 'N/A', '')
			unitObj.addAttribute('NRBTS_NAME', columnObj)

		if 'CELL_NAME' not in unitObj.attributes.keys():
			columnObj = column()
			columnObj.create('CELL_NAME', 'CELL_NAME', 'CELL_NAME', 'CELL_NAME', 'CELL_NAME', 'ENRICH',
			                 'VARCHAR2(255)', 'STRING', 'STRING', 'N/A', '')
			unitObj.addAttribute('CELL_NAME', columnObj)
		return

def enrich4G(unitObj, attrId):
		if attrId == 'MRBTS' and 'MRBTS_NAME' not in unitObj.attributes.keys():
			columnObj = column()
			columnObj.create('MRBTS_NAME', 'MRBTS_NAME', 'MRBTS_NAME', 'MRBTS_NAME', 'MRBTS_NAME', 'ENRICH', 'VARCHAR2(255)', 'STRING', 'STRING', 'N/A', '')
			unitObj.addAttribute('MRBTS_NAME', columnObj)
			return

		if attrId == 'LNBTS':
			if 'MRBTS_NAME' not in unitObj.attributes.keys():
				columnObj = column()
				columnObj.create('MRBTS_NAME', 'MRBTS_NAME', 'MRBTS_NAME', 'MRBTS_NAME', 'MRBTS_NAME', 'ENRICH', 'VARCHAR2(255)', 'STRING', 'STRING', 'N/A', '')
				unitObj.addAttribute('MRBTS_NAME', columnObj)

			if 'LNBTS_NAME' not in unitObj.attributes.keys():
				columnObj = column()
				columnObj.create('LNBTS_NAME', 'LNBTS_NAME', 'LNBTS_NAME', 'LNBTS_NAME', 'LNBTS_NAME', 'ENRICH', 'VARCHAR2(255)', 'STRING', 'STRING', 'N/A', '')
				unitObj.addAttribute('LNBTS_NAME', columnObj)

			return

		if attrId == 'LNCEL':
			if 'MRBTS_NAME' not in unitObj.attributes.keys():
				columnObj = column()
				columnObj.create('MRBTS_NAME', 'MRBTS_NAME', 'MRBTS_NAME', 'MRBTS_NAME', 'MRBTS_NAME', 'ENRICH',
				                 'VARCHAR2(255)', 'STRING', 'STRING', 'N/A', '')
				unitObj.addAttribute('MRBTS_NAME', columnObj)

			if 'LNBTS_NAME' not in unitObj.attributes.keys():
				columnObj = column()
				columnObj.create('LNBTS_NAME', 'LNBTS_NAME', 'LNBTS_NAME', 'LNBTS_NAME', 'LNBTS_NAME', 'ENRICH',
				                 'VARCHAR2(255)', 'STRING', 'STRING', 'N/A', '')
				unitObj.addAttribute('LNBTS_NAME', columnObj)

			if 'CELL_NAME' not in unitObj.attributes.keys():
				columnObj = column()
				columnObj.create('CELL_NAME', 'CELL_NAME', 'CELL_NAME', 'CELL_NAME', 'CELL_NAME', 'ENRICH', 'VARCHAR2(255)', 'STRING', 'STRING', 'N/A', '')
				unitObj.addAttribute('CELL_NAME', columnObj)
			return

def enrich3G(unitObj, attrId):
	if attrId == 'RNC' and 'RNC_NAME' not in unitObj.attributes.keys():
		columnObj = column()
		columnObj.create('RNC_NAME', 'RNC_NAME', 'RNC_NAME', 'RNC_NAME', 'RNC_NAME', 'ENRICH', 'VARCHAR2(255)', 'STRING', 'STRING', 'N/A', '')
		unitObj.addAttribute('RNC_NAME', columnObj)
		return

	if attrId == 'WBTS' and 'WBTS_NAME' not in unitObj.attributes.keys():
		columnObj = column()
		columnObj.create('WBTS_NAME', 'WBTS_NAME', 'WBTS_NAME', 'WBTS_NAME', 'WBTS_NAME', 'IENRICHD', 'VARCHAR2(255)', 'STRING', 'STRING', 'N/A', '')
		unitObj.addAttribute('WBTS_NAME', columnObj)
		return

	if attrId == 'WCEL':
		if 'CELLNAME ' not in unitObj.attributes.keys():
			columnObj = column()
			columnObj.create('CELLNAME', 'CELLNAME', 'CELLNAME', 'CELLNAME', 'CELLNAME', 'ENRICH', 'VARCHAR2(255)', 'STRING', 'STRING', 'N/A', '')
			unitObj.addAttribute('CELLNAME ', columnObj)
		if 'CELLID ' not in unitObj.attributes.keys():
			columnObj = column()
			columnObj.create('CELLID', 'CELLID', 'CELLID', 'CELLID', 'CELLID', 'IENRICHD', 'VARCHAR2(255)', 'STRING', 'STRING', 'N/A', '')
			unitObj.addAttribute('CELLID ', columnObj)
		return

def enrich2G(unitObj, attrId):
		if attrId == 'BSC' and 'BSC_NAME' not in unitObj.attributes.keys():
			columnObj = column()
			columnObj.create('BSC_NAME', 'BSC_NAME', 'BSC_NAME', 'BSC_NAME', 'BSC_NAME', 'ENRICH', 'VARCHAR2(255)', 'STRING', 'STRING', 'N/A', '')
			unitObj.addAttribute('BSC_NAME', columnObj)
			return

		if attrId == 'BTS':
			if 'BSC_NAME' not in unitObj.attributes.keys():
				columnObj = column()
				columnObj.create('BSC_NAME', 'BSC_NAME', 'BSC_NAME', 'BSC_NAME', 'BSC_NAME', 'ENRICH', 'VARCHAR2(255)', 'STRING', 'STRING', 'N/A', '')
				unitObj.addAttribute('BSC_NAME', columnObj)

			if 'BTS_NAME' not in unitObj.attributes.keys():
				columnObj = column()
				columnObj.create('BTS_NAME', 'BTS_NAME', 'BTS_NAME', 'BTS_NAME', 'BTS_NAME', 'ENRICH', 'VARCHAR2(255)', 'STRING', 'STRING', 'N/A', '')
				unitObj.addAttribute('BTS_NAME', columnObj)
			return

		if attrId == 'BCF':
			if 'BSC_NAME' not in unitObj.attributes.keys():
				columnObj = column()
				columnObj.create('BSC_NAME', 'BSC_NAME', 'BSC_NAME', 'BSC_NAME', 'BSC_NAME', 'ENRICH', 'VARCHAR2(255)', 'STRING', 'STRING', 'N/A', '')
				unitObj.addAttribute('BSC_NAME', columnObj)

			if 'BTS_NAME' not in unitObj.attributes.keys():
				columnObj = column()
				columnObj.create('BTS_NAME', 'BTS_NAME', 'BTS_NAME', 'BTS_NAME', 'BTS_NAME', 'ENRICH', 'VARCHAR2(255)', 'STRING', 'STRING', 'N/A', '')
				unitObj.addAttribute('BTS_NAME', columnObj)

			if 'CELLNAME' not in unitObj.attributes.keys():
				columnObj = column()
				columnObj.create('CELLNAME', 'CELLNAME', 'CELLNAME', 'CELLNAME', 'CELLNAME', 'ENRICH', 'VARCHAR2(255)', 'STRING', 'STRING', 'N/A', '')
				unitObj.addAttribute('CELLNAME', columnObj)

			if 'CELLID' not in unitObj.attributes.keys():
				columnObj = column()
				columnObj.create('CELLID', 'CELLID', 'CELLID', 'CELLID', 'CELLID', 'ENRICH', 'VARCHAR2(255)', 'STRING', 'STRING', 'N/A', '')
				unitObj.addAttribute('CELLID', columnObj)
			return
