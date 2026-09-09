#!/usr/bin/env python

__doc__ = \
    '''

'''

__version__ = '0.1'

__authors__ = [
    "Version 0.1: Andre barbosa <andre-g-barbosa@alticelabs.com>"
]

# Native libraries
import importlib
import re

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
    applied = False

    try:
        itemID = info["itemID"]
    except KeyError, e:
        logger.alert("KeyError: {0} is not a key".format(e))
        return applied
    except TypeError, e:
        logger.alert(e)
        return applied

    try:
        pattern = info["operation"].findall("regex")[0].attrib["pattern"]
        value = str(info["document"][itemID]).upper()

        if re.match(pattern, value):
            del info["document"][itemID]
            applied = True
    except TypeError, e:
        logger.alert(e)
        return applied
    except ValueError, e:
        logger.alert(e)
        return applied

    return applied
