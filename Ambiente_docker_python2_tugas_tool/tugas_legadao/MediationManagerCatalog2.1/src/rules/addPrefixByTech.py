__doc__ = \
    __version__ = '1.0'
__authors__ = ['Version 0.1: Marco jeronimo <marco-e-jeronimo@alticelabs.com>']

from lib.functions import validateSqlName


# #
# Adds a prefix in a field to depends on tech (using in RAN packs)
# #
def process(unitDict, config):
    for ossId in unitDict.keys():
        unitObj = unitDict[ossId]

        newPrefix = ""
        if 'R2G' == unitObj.tech:
            newPrefix = "CM2G_"
        if 'R3G' == unitObj.tech:
            newPrefix = "CM3G_"
        if 'R4G' == unitObj.tech:
            newPrefix = "CM4G_"
        if 'R5G' == unitObj.tech:
            newPrefix = "CM5G_"

        if config['field'] == 'name':
            unitObj.name = newPrefix + unitObj.name

        elif config['field'] == 'desc':
            unitObj.desc = newPrefix + unitObj.desc

        elif config['field'] == 'measuredObject':
            unitObj.measuredObject = newPrefix + unitObj.measuredObject

        else:
            for elementId in unitObj.tables.keys():
                elementObj = unitObj.tables[elementId]
                if config['field'] == 'typeId':
                    elementObj.typeId = newPrefix + elementObj.typeId

                elif config['field'] == 'ossId':
                    elementObj.ossId = newPrefix + elementObj.ossId

                elif config['field'] == 'sqlName':
                    elementObj.sqlName = newPrefix + elementObj.sqlName
                    elementObj.sqlName = validateSqlName(elementObj.sqlName)

                elif config['field'] == 'udn':
                    elementObj.udn = newPrefix + elementObj.udn

                else:
                    print '[Warning] Field "' + config['field'] + '" not found.'
