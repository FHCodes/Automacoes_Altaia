#!/usr/bin/env python

__doc__ = '''
'''

__version__ = '0.1'

__authors__ = [
    "Version 0.1: Rafael Gomes <rafael-g-gomes@telecom.pt>"
]

# Native libraries
import importlib
import pytz
import datetime

# Local libraries
logger = importlib.import_module("shelf.collectorprocess.logger").logger


def readOptions(xml):
    """
    This function gets a XML node with a recognized format.
    Transforms the information into a python dict and returns that dict.
    """

    return xml


def process(info, baseObject={}):
    # Check if operation has been badly placed in the operations catalog
    try:
        if info["familyObj"]:
            pass
    except KeyError:
        logger.error("Unit type operation convertTimezone, placed within an item in operations catalog.")
        return

    # Inicio do codigo final
    # format="%Y-%m-%d %H:%M:%S"
    field = info["operation"].findall("field")[0].text.upper()
    newField = info["operation"].findall("newField")[0].text.upper()

    for document in info["familyObj"].documents:
        # print info["familyObj"]
        for op in info["operation"].findall("def"):

            # Buscamos os parametros passados pela operacao
            try:
                tz_in = op.attrib["in_tz"]
                tz_out = op.attrib["out_tz"]
                format_in = op.attrib["in_pattern"]
                format_out = op.attrib["out_pattern"]
            except KeyError, e:
                logger.warning("KeyError: {0} is not a key".format(e))
                continue

            try:
                in_dt = pytz.timezone(tz_in).localize(datetime.datetime.strptime(document[field], format_in))
            except Exception, e:
                logger.warning("ERRO: " + str(e))
                continue
            try:
                out_dt = in_dt.astimezone(pytz.timezone(tz_out))
                out_dt = datetime.datetime.strftime(out_dt, format_out)
            except Exception, e:
                logger.warning("ERRO: " + str(e))
                continue

            document[newField] = str(out_dt)

    return info["familyObj"]
