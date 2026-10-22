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
    # allowedDocs = list()

    del info["familyObj"].documents[:]

    return info["familyObj"]
