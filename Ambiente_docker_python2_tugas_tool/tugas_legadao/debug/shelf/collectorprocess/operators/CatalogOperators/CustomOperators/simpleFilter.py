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
    return xml


def process(info, baseObject={}):
    # Check if operation has been badly placed in the operations catalog
    try:
        if info["familyObj"]:
            pass
    except KeyError:
        logger.error("Unit type operation simpleFilter, placed within an item in operations catalog.")
        return

    operation = info["operation"]

    allowedFields = dict()

    # For each fixedValue to add
    for allowed in operation.findall("allow"):
        allowedFields[allowed.text.strip().upper()] = ""

    for document in info["familyObj"].documents:
        # Get only allowed values from this document and create a new filtered document with them
        # Retrocompatible with Python < 2.7
        newDoc = dict((key, val) for (key, val) in document.items() if key in allowedFields)
        # Only compatible with python >= 2.7
        # newDoc = { key: val for key, val in document.items() if key in allowedFields }
        # Clear the current document
        document.clear()
        # Update the document with the allowed values only
        document.update(newDoc)

    return info["familyObj"]
