#!/usr/bin/env python

__doc__ = \
    '''

'''

__version__ = '0.1'

__authors__ = [
    "Version 0.1: Joao Pio <joao-t-pio@telecom.pt>"
]

# Native libraries
import importlib
import re

# Local libraries
logger = importlib.import_module("shelf.collectorprocess.logger").logger
FamilyObject = importlib.import_module("shelf.collectorprocess.operators.FamilyObject").FamilyObject


def readOptions(operation):
    """
		This function gets a XML node with a recognized format.
		Transforms the information into a python dict and returns that dict.
	"""

    return operation


def process(info, baseObject={}):
    try:

        # Check if operation has been badly placed in the operations catalog
        try:
            if info["familyObj"]:
                pass
        except KeyError:
            logger.error("Unit type operation unitSplit, placed within an item in operations catalog.")
            return

        familiobj_dict = dict()

        for field in info["operation"].findall("field"):
            itemid = field.get("id").upper()

            reg_dict = dict()
            for reg in field.findall("regex"):
                reg_dict[reg.get("newunit")] = reg.get("pattern")

            # print reg_dict.keys()
            for line in info["familyObj"].documents:
                if itemid not in line["data"].keys():
                    if info["familyObj"].unitID not in familiobj_dict.keys():
                        fo = FamilyObject()
                        fo.setUnitID(info["familyObj"].unitID)
                        fo.addDocument(line)
                        familiobj_dict[info["familyObj"].unitID] = fo
                        continue
                    else:
                        familiobj_dict[info["familyObj"].unitID].addDocument(line)
                        continue
                else:
                    foundMatch = False
                    for reg in reg_dict.keys():
                        rmatch = re.match(reg_dict[reg], line["data"][itemid])

                        if rmatch != None:

                            # print "Matched '{0}' with '{1}'".format(reg_dict[reg], line[itemid])

                            foundMatch = True
                            if reg not in familiobj_dict.keys():
                                fo = FamilyObject()
                                fo.setUnitID(reg)
                                fo.addDocument(line)
                                familiobj_dict[reg] = fo
                                continue
                            else:
                                familiobj_dict[reg].addDocument(line)
                                continue

                    if foundMatch == False:
                        if info["familyObj"].unitID not in familiobj_dict.keys():
                            fo = FamilyObject()
                            fo.setUnitID(info["familyObj"].unitID)
                            fo.addDocument(line)
                            familiobj_dict[info["familyObj"].unitID] = fo
                        else:
                            familiobj_dict[info["familyObj"].unitID].addDocument(line)


    except AttributeError, e:
        logger.warning(e)

    return familiobj_dict.values()
