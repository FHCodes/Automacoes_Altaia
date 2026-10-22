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
    operation = info["operation"]

    fieldsToCut = dict()

    # To limit warnings per family object
    warning_cache = []

    # For each fixedValue to add
    for fieldToCut in operation.findall("field"):
        fieldsToCut[fieldToCut.text.strip()] = ""

    for document in info["familyObj"].documents:
        # Get only allowed values from this document and create a new filtered document with them
        for key in fieldsToCut:
            try:
                del document[key]
            except KeyError:
                try:
                    del document[key.upper()]
                except KeyError:
                    if key not in warning_cache:
                        logger.warning("cutFields - field to cut {} not present in document.".format(key))
                        warning_cache.append(key)

                    continue

    return info["familyObj"]
