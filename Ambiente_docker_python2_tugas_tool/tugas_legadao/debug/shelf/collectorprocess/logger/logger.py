#!/usr/bin/env python

__doc__ = '''
'''

__version__ = '1.2'

__authors__ = [
    "Version 0.1: Francisco Santiago <francisco-j-santiago@telecom.pt>",
    "Version 1.2: Joao Pio <joao-t-pio@alticelabs.com>"
]

import logging
import os
import sys


class InfoFilter(logging.Filter):
    def filter(self, rec):
        return rec.levelno in (logging.DEBUG, logging.INFO)


# Logger level
logLevel = logging.INFO

# Registers a logger named "log"
logger = logging.getLogger("log")
# Sets the logging level for executions using the "log" logger
logger.setLevel(logLevel)

# Creates a formatter that defines how logging messages will be built
# formatter = logging.Formatter('[%(levelname)s]: %(message)s')
formatter = logging.Formatter('[%(levelname)s][%(tree)s]: %(message)s')

# Creates a stream channel for outputing logs. Used for console outputs in this case
ch_out = logging.StreamHandler(sys.stdout)
ch_out.setLevel(logLevel)
ch_out.setFormatter(formatter)
ch_out.addFilter(InfoFilter())

ch_err = logging.StreamHandler()
ch_err.setLevel(logging.WARNING)
ch_err.setFormatter(formatter)

# Adds the new handler to the logger
logger.addHandler(ch_out)
logger.addHandler(ch_err)

# This logger is a simple logger for regular "print" messages
printLogger = logging.getLogger("printlogger")
# Sets the logging level for executions using the "log" logger
printLogger.setLevel(logLevel)
# Creates a formatter that defines how logging messages will be built
formatterP = logging.Formatter('%(message)s')

# Creates a stream channel for outputing logs. Used for console outputs in this case
chp = logging.StreamHandler(sys.stdout)
chp.setLevel(logLevel)
chp.setFormatter(formatterP)

# Adds the new handler to the logger
printLogger.addHandler(chp)


def set_log_level(level):

    if level.upper() == "DEBUG":
        logger.setLevel(logging.DEBUG)
        ch_out.setLevel(logging.DEBUG)
    elif level.upper() == "INFO":
        logger.setLevel(logging.INFO)
        ch_out.setLevel(logging.INFO)
    elif level.upper() == "WARNING":
        logger.setLevel(logging.WARNING)
        ch_out.setLevel(logging.WARNING)
    elif level.upper() == "ERROR":
        logger.setLevel(logging.ERROR)
        ch_out.setLevel(logging.ERROR)


def build_tree(current_path):

    (path, file) = os.path.split(current_path)

    file = os.path.splitext(file)[0]

    path = path.split("/")

    for ind, element in enumerate(path):
        if element.upper() == "COLLECTORPROCESS":
            break

    path = path[ind+1:]
    path.append(file)

    return ".".join(path)


def debug(message, current_path=""):
    current_path = build_tree(current_path)
    logger.debug(message, extra={"tree": current_path})


def info(message, current_path=""):
    current_path = build_tree(current_path)
    logger.info(message, extra={"tree": current_path})


def warning(message, current_path=""):
    current_path = build_tree(current_path)
    logger.warning(message, extra={"tree": current_path})


def error(message, current_path=""):
    current_path = build_tree(current_path)
    logger.error(message, extra={"tree": current_path})


def printline(message): printLogger.info(message)


def toNA(message):
    init_tag = "[NA]"
    end_tag = "[/NA]"
    final_message = init_tag + message + end_tag
    logger.error(final_message)
