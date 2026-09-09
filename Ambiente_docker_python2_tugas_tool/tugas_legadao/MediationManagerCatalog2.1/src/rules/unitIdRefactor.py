__doc__ = \
    __version__ = '1.0'
__authors__ = ['Version 0.1: Joao Pio <joao-t-pio@alticelabs.com>']

import re


# #
# Refactors family IDs based on "search_regex" which finds patterns in the id and replaces them with "replacement_string"
# #
def process(unitDict, config):

    for ossId in unitDict.keys():
        # ID refactoring requires removing items from the dictionary since the id is the key
        unitObj = unitDict.pop(ossId)

        unitObj.ossId = re.sub(config["search_regex"], config["replacement_string"], unitObj.ossId)
        unitObj.typeId = re.sub(config["search_regex"], config["replacement_string"], unitObj.typeId)

        for tableId in unitObj.tables.keys():
            # ID refactoring requires removing items from the dictionary since the id is the key
            tableObj = unitObj.tables.pop(tableId)

            tableObj._ossId = re.sub(config["search_regex"], config["replacement_string"], tableObj._ossId)
            tableObj.typeId = re.sub(config["search_regex"], config["replacement_string"], tableObj.typeId)

            # Re inserts the table object with a new ID
            unitObj.tables[tableObj._ossId] = tableObj

        # Re inserts the unitObj with a new id
        unitDict[unitObj.ossId] = unitObj