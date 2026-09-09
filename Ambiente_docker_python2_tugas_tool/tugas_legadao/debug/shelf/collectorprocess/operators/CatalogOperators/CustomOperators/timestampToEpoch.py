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
import time
import re

# Local libraries
logger = importlib.import_module("shelf.collectorprocess.logger").logger


def readOptions(xml):
    """
		This function gets a XML node with a recognized format.
		Transforms the information into a python dict and returns that dict.
	"""

    return xml


def process(info, baseObject={}):
    applied = False

    try:
        value = info["document"][info["itemID"]]

        dest_node = info["operation"].find("newField")
        dest = dest_node.text

        pattern = '%Y-%m-%d %H:%M:%S.%f'

        # Select the corresponding timestamp pattern
        if re.match(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$", value):
            pattern = '%Y-%m-%d %H:%M'
        elif re.match(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$", value):
            pattern = '%Y-%m-%d %H:%M:%S'
        elif re.match(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}.\d+$", value):
            pattern = '%Y-%m-%d %H:%M:%S.%f'

        # Try to match first timestamp with miliseconds
        epoch = int(time.mktime(time.strptime(value, pattern)))

        info["document"][dest] = epoch

        applied = True
    except TypeError, e:
        logger.warning("TypeError - {0}".format(e))
        return applied
    except ValueError, e:
        logger.warning("ValueError - {0}".format(e))
        return applied

    return applied
