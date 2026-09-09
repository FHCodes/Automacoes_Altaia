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
import re

# Local libraries
logger = importlib.import_module("shelf.collectorprocess.logger").logger


def readOptions(xml):
    """
		This function gets a XML node with a recognized format.
		Transforms the information into a python dict and returns that dict.
	"""
    return xml


def regex(document, filt):
    result = None

    pattern = filt.attrib["pattern"]
    field = filt.attrib["field"].upper()

    if field in document["data"] and re.match(pattern, document["data"][field]):
        result = True
    else:
        result = False

    return result


def process(info, baseObject={}):
    operation = info["operation"]

    viableDocs = list()
    thisModulesMethods = globals()

    for document in info["familyObj"].documents:
        # For each fixedValue to add
        for filt in operation.findall("filter"):
            if filt.attrib["by"] in thisModulesMethods:
                docPassed = thisModulesMethods["regex"](document, filt)
            else:
                logger.warning("Filter by '{0}' does not exist in CatalogOperators".format(filt.attrib["by"]))

            if docPassed is True:
                viableDocs.append(document)

    # Recreate document list in familyObject containing only approved docs
    info["familyObj"].clearDocuments()
    for document in viableDocs:
        info["familyObj"].addDocument(document)

    return info["familyObj"]
