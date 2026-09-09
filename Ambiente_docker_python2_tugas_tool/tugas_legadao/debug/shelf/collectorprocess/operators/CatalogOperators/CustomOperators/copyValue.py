#!/usr/bin/env python

__doc__ = \
    '''

'''

__version__ = '0.1'

__authors__ = [
    "Version 0.1: Joao Pio <joao-t-pio@telecom.pt>"
]

def readOptions(xml):
    """
    This function gets a XML node with a recognized format.
    Transforms the information into a python dict and returns that dict.
    """

    return xml


def process(info, baseObject={}):
    itemID = info["itemID"].upper()

    for newFieldID in info["operation"].findall("newField"):
        info["document"][newFieldID.text.upper()] = info["document"][itemID]

    return True
