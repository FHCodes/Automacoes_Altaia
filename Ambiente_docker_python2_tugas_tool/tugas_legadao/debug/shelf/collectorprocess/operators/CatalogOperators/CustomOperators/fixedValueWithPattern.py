#!/usr/bin/env python

__doc__ = \
    '''

'''

__version__ = '0.1'

__authors__ = [
    "Version 0.1: Ricardo Auxiliar <ricardo-d-auxiliar@alticelabs.com>"
]

# Native libraries
import importlib
import re

# Local libraries
logger = importlib.import_module("shelf.collectorprocess.logger").logger


def readOptions(operation):
    """
		This function gets a XML node with a recognized format.
		Transforms the information into a python dict and returns that dict.
	"""
    options = {
        "regexNodes": list()
    }

    for regexNode in operation.findall("regex"):
        regNode = {
            "regex": re.compile(regexNode.attrib["pattern"], re.IGNORECASE),
            "newFields": [newField for newField in regexNode.findall("newField")]
        }

        options["regexNodes"].append(regNode)

    return options


def process(info, baseObject={}):
    matched = False
    added = False
    valueToTest = info["document"][info["itemID"]]

    # Checks every REGEX group until one of them matches the string to be tested
    for regexNode in info["operation"]["regexNodes"]:
        try:
            # Test regex into dictionary of named groups
            for m in regexNode["regex"].finditer(valueToTest):
                matched = True
                for field in regexNode["newFields"]:
                    if field.get("value"):
                        info['document'].update({field.text.upper(): field.get("value")})

        except re.error, e:
            logger.alert(e)

    if not matched:
        logger.warning(
            "Could not match regex of item '{0}' in unit '{1}' with string '{2}' in operator fixedValueWithPattern".format(
                info["itemID"], info["unitID"], info["document"][info["itemID"]]))

    return matched
