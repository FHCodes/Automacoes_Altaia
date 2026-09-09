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

    return options


def process(info, baseObject={}):
    applied = False

    try:
        itemID = info["itemID"]
    except KeyError, e:
        logger.warning("KeyError: {0} is not a key".format(e))
        return applied
    except TypeError, e:
        logger.warning(e)
        return applied

    try:
        if info["document"][itemID] != '' and info["document"][itemID] != None:
            i = int(info["document"][itemID], 16)
            info["document"].update({itemID: str(i)})
            applied = True
        else:
            # logger.warning("LAC isn't exist in document")
            pass
    except TypeError, e:
        logger.warning(e)
        return applied
    except ValueError, e:
        logger.warning(e)
        return applied

    return applied
