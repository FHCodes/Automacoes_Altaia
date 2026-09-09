#!/usr/bin/env python

__doc__ = '''
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
    try:
        itemID = info["itemID"]
        valueToReplace = info["document"][itemID]
    except KeyError, e:
        logger.alert("KeyError: {0} is not a key".format(e))
        return False
    except TypeError, e:
        logger.alert(e)
        return False

    # Checks every item in the dictionary and replaces it in the document (if it exists)
    for item in info["operation"].findall("item"):
        try:
            if valueToReplace == item.find("key").text:
                info["document"].update({itemID: item.find("value").text})
                return True
        except AttributeError, e:
            logger.alert(e)
            return False

    return False
