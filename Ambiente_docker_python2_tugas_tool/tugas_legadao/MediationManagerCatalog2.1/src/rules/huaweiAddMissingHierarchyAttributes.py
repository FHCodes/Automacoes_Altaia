__doc__ = \
	__version__ = '1.0'
__authors__ = ['Version 0.1: Marco Jeronimo <marco-a-jeronimo@alticelabs.com>']

# #
# Add to catalogs all missing atributes of hierarchy
# #
from lib.objects.column import column
from collections import OrderedDict

def process(unitDict, config):
    for ossId in unitDict.keys():
        unitObj = unitDict[ossId]

        for tableId in unitObj.tables.keys():
            tableObj = unitObj.getTable(tableId)
            if '2G' in unitObj.tech:
                if "CELL_NAME" in unitObj.getAttributes():
                    if "BTS_NAME" not in unitObj.getAttributes():
                        unitObj.addAttribute('BTS_NAME', createColumn('BTS_NAME'))
                    if "BSC_NAME" not in unitObj.getAttributes():
                        unitObj.addAttribute('BSC_NAME', createColumn('BSC_NAME'))
                elif "BTS_NAME" in unitObj.getAttributes():
                    if "BSC_NAME" not in unitObj.getAttributes():
                        unitObj.addAttribute('BSC_NAME', createColumn('BSC_NAME'))
                elif '_Node' in unitObj.get('ab').value:
                    unitObj.addAttribute('BTS_NAME', createColumn('BTS_NAME'))
                    if "BSC_NAME" not in unitObj.getAttributes():
                        unitObj.addAttribute('BSC_NAME', createColumn('BSC_NAME'))

            if '3G' in unitObj.tech:
                if 'CELL_NAME' in unitObj.getAttributes():
                    if 'NODEB_NAME' not in unitObj.getAttributes():
                        unitObj.addAttribute('NODEB_NAME', createColumn('NODEB_NAME'))
                    if 'RNC_NAME' not in unitObj.getAttributes():
                        unitObj.addAttribute('RNC_NAME', createColumn('RNC_NAME'))
                elif 'NODEB_NAME' in unitObj.getAttributes():
                    if "RNC_NAME" not in unitObj.getAttributes():
                        unitObj.addAttribute('RNC_NAME', createColumn('RNC_NAME'))
                elif '_Node' in unitObj.get('ab').value:
                    unitObj.addAttribute('NODEB_NAME', createColumn('NODEB_NAME'))
                    if 'RNC_NAME' not in unitObj.getAttributes():
                        unitObj.addAttribute('RNC_NAME', createColumn('RNC_NAME'))

            if '4G' in unitObj.tech:
                if 'CELL_NAME' in unitObj.getAttributes():
                    if 'ENODEB_NAME' not in unitObj.getAttributes():
                        unitObj.addAttribute('ENODEB_NAME', createColumn('ENODEB_NAME'))
                if '_Node' in unitObj.get('ab').value:
                    if 'ENODEB_NAME' not in unitObj.getAttributes():
                        unitObj.addAttribute('ENODEB_NAME', createColumn('ENODEB_NAME'))
            if '5G' in unitObj.tech:
                if 'CELL_NAME' in unitObj.getAttributes():
                    if 'GNODEB_NAME' not in unitObj.getAttributes():
                        unitObj.addAttribute('GNODEB_NAME', createColumn('GNODEB_NAME'))
                if '_Node' in unitObj.get('ab').value:
                    if 'GNODEB_NAME' not in unitObj.getAttributes():
                        unitObj.addAttribute('GNODEB_NAME', createColumn('GNODEB_NAME'))



def createColumn(name):
	columnObj = column()
	columnObj.create(name, name, name, name, name, 'ID', 'VARCHAR2(256)', 'STRING', 'STRING', '', '')
	return columnObj