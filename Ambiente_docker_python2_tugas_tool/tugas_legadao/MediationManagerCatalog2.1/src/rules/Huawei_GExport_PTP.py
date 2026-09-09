__doc__ = \
    __version__ = '1.0'
__authors__ = ['Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>']

from lib.objects.column import column
from collections import OrderedDict


# #
#
# #
def process(unitDict, config):
    for ossId in unitDict.keys():
        unitObj = unitDict[ossId]

        for tableId in unitObj.tables.keys():
            tableObj = unitObj.getTable(tableId)
            if '2G' in unitObj.tech:
                createLevel(unitObj, tableObj, ['BSC_NAME'], ['BTS_NAME'], ['CELL_NAME', 'Cell_Id'],  ['BSC_NAME'])
            if '3G' in unitObj.tech:
                createLevel(unitObj, tableObj, ['RNC_NAME'], ['NODEB_NAME'], ['CELL_NAME', 'Cell_Id'], ['RNC_NAME'])
            if '4G' in unitObj.tech:
                createLevel(unitObj, tableObj, [], ['ENODEB_NAME'], ['CELL_NAME', 'Cell_Id'], ['ENODEB_NAME'])
            if '5G' in unitObj.tech:
                createLevel(unitObj, tableObj, [], ['GNODEB_NAME'], ['CELL_NAME', 'Cell_Id'], ['GNODEB_NAME'])
            if 'Site' in unitObj.tech:
                createLevel(unitObj, tableObj, [], [], ['CELL_NAME', 'Cell_Id'], [])



def createLevel(unitObj, tableObj, findController, findSite, findCell, toName):
    CELLID = {'CELLID', 'LOCALCELLID', 'LOCELL', 'ULOCELLID', 'ULOCELL', 'GLOCELLID', 'CELLNAME', 'LOCALCELLNAME',
              'SRC2GNCELLID', 'SRC3GNCELLID', 'SRCLTENCELLID', 'INNCELLID', 'PRIMARYLOCALCELLID', 'NRCELLID',
              'NRDUCELLID', 'LOCELLIDLISTTYPE.ULOCELLID'}
    SITE = {'BTSNAME', 'BTSID', 'NODEBNAME', 'NODEBID', 'ENODEBID', 'ENODEBNAME', 'GBTSFUNCTIONNAME',
            'NODEBFUNCTIONNAME', 'ENODEBFUNCTIONNAME', 'GNODEBFUNCTIONNAME', 'GNBID'}
    CONTROLLER = {'BSCID', 'BSCIDX', 'BSCTID', 'LOCALBSCID', 'BSCNAME', 'RNCID', 'RNCNAME', 'LOGICRNCID'}

    toSite = False
    toCell = False

    extra = unitObj.getExtraCatalog('oss')
    # if '_NODEBFUNCTION' in extra['ab'].value.upper() or '_ENODEBFUNCTION' in extra['ab'].value.upper() or '_GBTSFUNCTION' in extra['ab'].value.upper() or '_GNODEBFUNCTION' in extra['ab'].value.upper():
    #	toFileName = True
    for name in toName:
        unitObj.addAttribute(name, createColumn(name))

    x = unitObj.attributes.keys()
    x.extend(tableObj.counters.keys())

    if set(list(CELLID.intersection(x))) != set([]):
        toCell = True
        for name in findCell:
            unitObj.addAttribute(name, createColumn(name))

    if set(list(SITE.intersection(x))) != set([]) and not toCell:
        toSite = True
        for name in findSite:
            unitObj.addAttribute(name, createColumn(name))

    if set(list(CONTROLLER.intersection(x))) != set([]) and not toSite:
        for name in findController:
            unitObj.addAttribute(name, createColumn(name))


# if not toController and not toCell and not toSite and not toFileName:
#	unitObj.addAttribute('NE_NAME', createColumn('NE_NAME'))

def createColumn(name):
    columnObj = column()
    columnObj.create(name.upper(), name.upper(), name, name.upper(), name.upper(), 'ID', 'VARCHAR2(256)', 'STRING', 'STRING', '', '')
    return columnObj
