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

# Local libraries
logger = importlib.import_module("shelf.collectorprocess.logger").logger


def readOptions(xml):
    """
		This function gets a XML node with a recognized format.
		Transforms the information into a python dict and returns that dict.
	"""
    options = dict()

    return xml


def process(info, baseObject={}):
    added = False

    try:
        unitID = info["familyObj"].unitID
        operation = info["operation"]
    except KeyError, e:
        logger.warning("KeyError: {0} is not a key".format(e))
        return info["familyObj"]
    except TypeError, e:
        logger.warning(e)
        return info["familyObj"]

    # For each fixedValue to add
    for newValue in operation.findall("newField"):
        try:
            # for each document in the familyObj add the fixed value
            for document in info["familyObj"].documents:
                document[newValue.text.upper()] = newValue.get("value")
            added = True
        except AttributeError, e:
            logger.warning(e)
            return info["familyObj"]

    if not added:
        logger.warning("Could not add fixedValue of unit '{0}'".format(unitID))

    return info["familyObj"]
