#!/usr/bin/env python

__doc__ = \
    '''
'''

__version__ = '0.1'

__authors__ = [
    "Version 0.1: Joao Pio <joao-t-pio@telecom.pt>"
]

from datetime import datetime, timedelta


def readOptions(xml):
    """
    This function gets a XML node with a recognized format.
    Transforms the information into a python dict and returns that dict.
    """

    return xml


def process(info, baseObject={}):
    timestamp = datetime.now()

    field = info["operation"].findall("field")[0].text.upper()
    newField = info["operation"].findall("newField")[0].text.upper()

    for document in info["familyObj"].documents:

        # Run the defined operations
        for op in info["operation"].findall("def"):

            # Get the needed value from the current document
            timestamp = datetime.strptime(document[field], op.attrib["pattern"])

            if op.attrib["type"] == "subtract":
                timedeltaParams = {op.attrib["datecomponent"]: int(op.attrib["amount"])}
                # Pass timedeltaParams as kwargs to timedelta
                timestamp = timestamp - timedelta(**timedeltaParams)
            elif op.attrib["type"] == "add":
                timedeltaParams = {op.attrib["datecomponent"]: int(op.attrib["amount"])}
                # Pass timedeltaParams as kwargs to timedelta
                timestamp = timestamp + timedelta(**timedeltaParams)

            document[newField] = timestamp.strftime(op.attrib["pattern"])

    return info["familyObj"]
