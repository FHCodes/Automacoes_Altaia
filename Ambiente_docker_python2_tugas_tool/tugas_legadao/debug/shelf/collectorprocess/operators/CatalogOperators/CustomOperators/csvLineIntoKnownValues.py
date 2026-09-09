#!/usr/bin/env python

__doc__ = \
    '''

'''

__version__ = '0.1'

__authors__ = [
    "Version 0.1: Francisco Santiago <francisco-j-santiago@telecom.pt>"
]


def readOptions(operation):
    """
    This function gets a XML node with a recognized format.
    Transforms the information into a python dict and returns that dict.
    """
    options = {
        "newFields": [newField.text.strip() for newField in operation.findall("newField")]
    }

    return options


def process(info, baseObject={}):
    """
    info = {
         "document": dict(),
         "itemID": str(),
         "unitID": str(),
         "operation": ElementTree.Element()
    """

    # Gets a list of item names
    knownFields = [newField.strip().upper() for newField in info["operation"]["newFields"]]
    # Generates a list of values after splitting the target by the given delimiter
    values = info["document"][info["itemID"]].split(",")

    # Unites the item names with the corresponding values, filling only as many names as values available
    newValuesDocument = dict(zip(knownFields, values))

    info["document"].update(newValuesDocument)

    return True
