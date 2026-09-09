#!/usr/bin/env python

__version__ = '0.1'

__authors__ = [
    "Version 0.1: Francisco Santiago <francisco-j-santiago@telecom.pt>"
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
            "newFields": [newField.text.upper() for newField in regexNode.findall("newField")]
        }

        options["regexNodes"].append(regNode)

    return options


def process(info, baseObject={}):
    matched = False
    valueToTest = info["document"][info["itemID"]]

    # Checks every REGEX group until one of them matches the string to be tested
    for regexNode in info["operation"]["regexNodes"]:

        try:

            # Test regex into dictionary of named groups
            matches = [m.groupdict() for m in regexNode["regex"].finditer(valueToTest)]

            # Check if any was successfull
            if matches:

                matches = [(key.upper(), value) for key, value in matches[0].items()]

                info["document"].update(dict(matches))

                matched = True

                break

            else:
                # Create empty entries for the fields now matched, unless they are already in the dict
                [info["document"].setdefault(newField, "") for newField in regexNode["newFields"] if
                 newField not in info["document"]]

        except re.error, e:
            logger.alert(e)

    if not matched:
        logger.warning(
            "Could not match regex of item '{0}' in unit '{1}' with string '{2}'".format(info["itemID"], info["unitID"],
                                                                                         info["document"][
                                                                                             info["itemID"]]))

    return matched
