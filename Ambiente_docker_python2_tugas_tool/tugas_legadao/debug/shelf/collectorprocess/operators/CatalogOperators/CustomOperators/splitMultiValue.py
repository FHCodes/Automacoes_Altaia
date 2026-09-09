#!/usr/bin/env python

__doc__ = \
    '''

'''

__version__ = '0.2'

__authors__ = [
    "Version 0.1: Rafael Gomes <rafael-g-gomes@alticelabs.pt>"
    "Version 0.2: Joao Pio <joao-t-pio@alticelabs.pt>"
]

# Native libraries
import importlib
import itertools

# Local libraries
logger = importlib.import_module("shelf.collectorprocess.logger").logger


def readOptions(xml):
    """
		This function gets a XML node with a recognized format.
		Transforms the information into a python dict and returns that dict.
	"""

    return xml


def process(info, baseObject={}):
    # Item Id to be processed
    try:
        itemID = info["itemID"]
    # print "DEBUG: Item Id - {}".format(itemID)
    except:
        logger.warning("splitMultiValue: Missing Item Id")
        return info

    try:
        valueToSplit = info["document"][info["itemID"]]
    # print "DEBUG: valueToSplit - {}".format(valueToSplit)
    except KeyError:
        logger.warning("splitMultiValue: Could not get value in document for Item {}".format(itemID))
        return info

    splitNode = info["operation"].find("split")

    if splitNode:
        delimiter = splitNode.attrib["delimiter"]
    else:
        logger.warning(
            "splitMultiValue: Could not get the delimiter character for item {}. Default value = ','".format(itemID))
        delimiter = ','

    if "compressed" in info["operation"].keys():
        compressed = info["operation"].attrib["compressed"]
    else:
        logger.warning(
            "splitMultiValue: Could not get the compressed mode for item {}. Default value = 'false'".format(itemID))
        compressed = "False"

    if compressed == "True":
        # Break the value by the delimiter character
        splitValues = valueToSplit.split(delimiter)
        # Get the number of counters in the string
        num_counters = splitValues[0]
        # Slice the values to exclude the number of counters
        splitValues = splitValues[1:]

        if num_counters == "0":
            return info

        else:
            # Turns the list into a dictionary where the first element of a pair is the key and the second is the value
            # EXAMPLE: [12, 3322, 15, 323, 250, 1] -> {250: 1, 12: 3322, 15: 323}
            splitValues = dict(itertools.izip_longest(*[iter(splitValues)] * 2, fillvalue=""))

            # Build an indexed dictionary with the counter names
            # EXAMPLE: {0: pmSessionTimeDrbQciSub0, 1: pmSessionTimeDrbQciSub1, 2: pmSessionTimeDrbQciSub2}

            # Retrocompatible with Python < 2.7
            newFields = dict((index, name) for (index, name) in
                             enumerate([newField.text.upper() for newField in splitNode.findall("newField")]))
            # Only compatible with python >= 2.7
            # newFields = {index : name for index, name in enumerate([ newField.text.upper() for newField in splitNode.findall("newField") ])}

            newDocument = {}

            for counter_index in splitValues.keys():
                try:
                    newDocument[newFields[int(counter_index)]] = splitValues[counter_index]
                except:
                    logger.warning(
                        "Could not split values because one or more fields are emptys \"{0}\": ".format(splitValues))
                    continue

            # Update the document with the newly obtained fields (keeps the other values)
            info["document"].update(newDocument)

    else:

        list_newFields = [newField.text.upper() for newField in splitNode.findall("newField")]

        # Break the value by the delimiter character
        splitValues = valueToSplit.split(delimiter)
        if ' ' in splitValues:
            splitValues = ['' if x in ' ' else x for x in splitValues]
        # for i in range(len(splitValues)):
        #	if splitValues[i] == ' ':
        #		splitValues[i]=''
        # print splitValues
        # Create a new dictionary with the information separated by delimiter
        if len(list_newFields) > len(splitValues):
            # logger.warning("splitMultiValue: The number of subcounters {0} of counterID {1} is major that the number of values  {2} for them {3}!!!!!. ".format(len(list_newFields),itemID,len(splitValues),valueToSplit))
            listacompleta = map(lambda x, y: y if x is None else x, splitValues, [""] * len(list_newFields))
            new_documents = dict(zip(list_newFields, listacompleta))
        elif len(list_newFields) < len(splitValues):
            logger.warning(
                "splitMultiValue: The number of subcounters {0} of counterID {1} is menor that the number of values {2} for them {3} !!!!!. ".format(
                    len(list_newFields), itemID, len(splitValues), valueToSplit))
            new_documents = dict(zip(list_newFields, splitValues[0:len(list_newFields)]))
        else:
            new_documents = dict(zip(list_newFields, splitValues))

        # Update the document with the newly obtained fields (keeps the other values)
        info["document"].update(new_documents)

    return info
