#!/usr/bin/env python

__doc__ = '''
'''

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

    return operation


def process(info, baseObject={}):
    # Check if operation has been badly placed in the operations catalog
    try:
        if info["familyObj"]:
            pass
    except KeyError:
        logger.error("Unit type operation concatFields, placed within an item in operations catalog.")
        return

    # String to be generated from specified document fields, according to pattern specified in 'stringfromfields' operation attribute
    stringfromfields = ""
    # The regex pattern to be used to filter stringfromfields
    pattern = ""
    # The final string that derives from the pattern application to the stringfromfields
    finalstring = ""
    # Document fields to be used to generate stringfromfields
    fields = list()
    # Final field where the operation result will be put
    newField = ""
    nullable = False

    for definition in info["operation"].findall("def"):

        stringfromfields = definition.attrib["stringfromfields"]

        if "pattern" in definition.attrib and "finalstring" in definition.attrib:
            pattern = definition.attrib["pattern"]
            finalstring = definition.attrib["finalstring"]

        if "nullable" in definition.attrib:
            nullablestr = definition.attrib["nullable"]
            if nullablestr.upper() == 'TRUE' or nullablestr.upper() == 'YES':
                nullable = True
            else:
                nullable = False
        else:
            nullable = False

        for field in definition.findall("field"):
            fields.append(field.text.strip().upper())

        for newFieldFromDef in definition.findall("newField"):
            newField = newFieldFromDef.text.strip().upper()

    for document in info["familyObj"].documents:
        fieldValues = [document[field] if field in document else "" for field in fields]

        if not nullable:
            tempString = stringfromfields.format(*fieldValues)

            if pattern and finalstring:
                document[newField] = re.sub(pattern, finalstring, tempString)
            else:
                document[newField] = tempString

        elif nullable:
            tempString = []

            if pattern:
                for field in fieldValues:
                    try:
                        tempString.append(re.search(pattern, field).group(1))
                    except:
                        tempString.append(None)

                if (len(tempString) - tempString.count(None) == 1):
                    document[newField] = list(filter(None, tempString))[0]

                elif (len(tempString) - tempString.count(None) == 0):
                    document[newField] = ""

                else:
                    document[newField] = stringfromfields.format(*tempString)
            else:
                document[newField] = ""

    return info["familyObj"]
