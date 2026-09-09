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
    convertToValues = ["B", "K", "M", "G"]

    try:
        itemID = info["itemID"]
    except KeyError, e:
        logger.alert("KeyError: {0} is not a key".format(e))
        return applied
    except TypeError, e:
        logger.alert(e)
        return applied

    try:
        convertTo = info["operation"].findall("convertTo")[0].text.upper()
        value = str(info["document"][itemID]).upper()

        if convertTo not in convertToValues:
            logger.alert("Invalid convertTo value: {0}".format(convertTo))
            return applied

        if convertTo == "B":

            if value.endswith("G"):
                if value.split("G")[0].replace('.', '', 1).isdigit():
                    value = float(value.split("G")[0]) * 1024 * 1024 * 1024
            elif value.endswith("M"):
                if value.split("M")[0].replace('.', '', 1).isdigit():
                    value = float(value.split("M")[0]) * 1024 * 1024
            elif value.endswith("K"):
                if value.split("K")[0].replace('.', '', 1).isdigit():
                    value = float(value.split("K")[0]) * 1024
            elif value.endswith("B"):
                if value.split("B")[0].replace('.', '', 1).isdigit():
                    value = float(value.split("B")[0])
            elif value.replace('.', '', 1).isdigit():
                pass
            else:
                value = ""

        elif convertTo == "K":

            if value.endswith("G"):
                if value.split("G")[0].replace('.', '', 1).isdigit():
                    value = float(value.split("G")[0]) * 1024 * 1024
            elif value.endswith("M"):
                if value.split("M")[0].replace('.', '', 1).isdigit():
                    value = float(value.split("M")[0]) * 1024
            elif value.endswith("K"):
                if value.split("K")[0].replace('.', '', 1).isdigit():
                    value = value.replace("K", "", 1)
            elif value.endswith("B"):
                if value.split("B")[0].replace('.', '', 1).isdigit():
                    value = float(value.split("B")[0]) / 1024
            elif value.replace('.', '', 1).isdigit():
                pass
            else:
                value = ""

        elif convertTo == "M":

            if value.endswith("G"):
                if value.split("G")[0].replace('.', '', 1).isdigit():
                    value = float(value.split("G")[0]) * 1024
            elif value.endswith("M"):
                if value.split("M")[0].replace('.', '', 1).isdigit():
                    value = value.replace("M", "", 1)
            elif value.endswith("K"):
                if value.split("K")[0].replace('.', '', 1).isdigit():
                    value = float(value.split("K")[0]) / 1024
            elif value.endswith("B"):
                if value.split("B")[0].replace('.', '', 1).isdigit():
                    value = float(value.split("B")[0]) / (1024 * 1024)
            elif value.replace('.', '', 1).isdigit():
                pass
            else:
                value = ""

        elif convertTo == "G":

            if value.endswith("G"):
                if value.split("G")[0].replace('.', '', 1).isdigit():
                    value = value.replace("G", "", 1)
            elif value.endswith("M"):
                if value.split("M")[0].replace('.', '', 1).isdigit():
                    value = float(value.split("M")[0]) / 1024
            elif value.endswith("K"):
                if value.split("K")[0].replace('.', '', 1).isdigit():
                    value = float(value.split("K")[0]) / (1024 * 1024)
            elif value.endswith("B"):
                if value.split("B")[0].replace('.', '', 1).isdigit():
                    value = float(value.split("B")[0]) / (1024 * 1024 * 1024)
            elif value.replace('.', '', 1).isdigit():
                pass
            else:
                value = ""

        info["document"].update({itemID: value})
        applied = True
    except TypeError, e:
        logger.alert(e)
        return applied
    except ValueError, e:
        logger.alert(e)
        return applied

    return applied
