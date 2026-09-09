#!/usr/bin/env python

__doc__ = \
    '''

'''

__version__ = '0.1'

__authors__ = [
    "Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>"
]

# Native libraries
import importlib

# Local libraries
logger = importlib.import_module("shelf.collectorprocess.logger").logger


def readOptions(operation):
    """
		This function gets a XML node with a recognized format.
		Transforms the information into a python dict and returns that dict.
	"""
    return operation


def process(info, baseObject={}):
    itemID = info["itemID"].upper()
    # Checks every def to be applied
    for definition in info["operation"].findall("def"):
        startIndex = int((definition).attrib["startIndex"])
        endIndex = int((definition).attrib["endIndex"])
        # Checks every newField and copies the value trucated to them
        for newFieldID in definition.findall("newField"):
            info["document"][newFieldID.text.upper()] = info["document"][itemID][startIndex:endIndex]

    return True
