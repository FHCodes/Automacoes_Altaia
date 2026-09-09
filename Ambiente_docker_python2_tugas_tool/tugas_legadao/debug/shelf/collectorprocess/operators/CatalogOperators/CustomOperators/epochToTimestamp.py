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
import datetime

# Local libraries
logger = importlib.import_module("shelf.collectorprocess.logger").logger


def readOptions(xml):
    """
		This function gets a XML node with a recognized format.
		Transforms the information into a python dict and returns that dict.
	"""

    return xml


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
        value = info["document"][info["itemID"]]

        if len(value) > 10:
            newValue = int(value[:10])
        else:
            newValue = int(value)

        newValue = datetime.datetime.fromtimestamp(newValue)
        newValue = newValue.strftime('%Y-%m-%d %H:%M:%S')
        info["document"].update({itemID: newValue})

        applied = True
    except TypeError, e:
        logger.warning(e)
        return applied
    except ValueError, e:
        logger.warning(e)
        return applied

    return applied
