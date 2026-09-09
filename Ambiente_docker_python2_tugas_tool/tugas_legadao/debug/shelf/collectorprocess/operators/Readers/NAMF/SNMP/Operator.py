#!/usr/bin/env python

__doc__ = \
    '''
    NAMF SNMP CSV files reader
'''

__version__ = '1.0'

__authors__ = [
    "Version 0.1: Joao Pio <joao-t-pio@alticelabs.com>"
]

import json
import os
import re
import importlib
from csv import reader
from datetime import datetime

# Local libraries
BaseOperator = importlib.import_module("shelf.collectorprocess.operators.BaseOperator").BaseOperator
FamilyObject = importlib.import_module("shelf.collectorprocess.operators.FamilyObject").FamilyObject
logger = importlib.import_module("shelf.collectorprocess.logger").logger


class Operator(BaseOperator):

    # Class Constructor
    def __init__(self, operationParams, baseObject={}):
        BaseOperator.__init__(self, operationParams, baseObject=baseObject)

        self.filename_regex = re.compile(r'^.+_(?P<date>\d+).csv$')

        self.pre_replace = None
        self.decode_func = self.__decode_line_values

        if 'pre_replace' in self.options:
            try:
                self.pre_replace = json.loads(self.options['pre_replace'])
            except Exception:
                self.pre_replace = None

        if 'strip_values' in self.options:
            try:
                self.decode_func = self.__decode_and_strip_line_values if self.options['strip_values'].lower() == 'true' else self.__decode_line_values
            except Exception:
                self.decode_func = self.__decode_line_values

    @staticmethod
    def __decode_line_values(line):
        return [item.decode("utf-8") for item in line]

    @staticmethod
    def __decode_and_strip_line_values(line):
        return [item.decode("utf-8").strip() for item in line]

    def pre_replace_process(self, data_string):
        for k, v in self.pre_replace.items():
            try:
                data_string = data_string.replace(k.encode(), v.encode())
            except Exception as ex:
                logger.warning("Exception replacing \"{0}\" for \"{1}\" in csv data: {2}".format(k, v, ex), __file__)

        for line in data_string.splitlines():
            yield line

    # ------------------------------------------------------------------------------------------------------------------

    def process(self, familyObj=FamilyObject(), baseObject={}):

        logger.debug("Reading SNMP CSV file contents...", __file__)
        files_to_process = familyObj.getFiles()

        # Clear used information
        familyObj.clearFiles()
        familyObj.clearDocuments()

        for file_path in files_to_process:

            # Get file's name to find the unitID
            file_name = os.path.basename(file_path)

            file_name_match = self.filename_regex.match(file_name)

            if file_name_match is None:
                logger.warning("Could not recognize file name format for file: {0}".format(file_name), __file__)
                continue

            date = file_name_match.group("date")

            # Parse and change datetime format
            date = datetime.strptime(date, "%Y%m%d%H%M")
            date = datetime.strftime(date, "%Y-%m-%d %H:%M:%S")

            # get the unit from the folder name
            try:
                unit_id = os.path.dirname(file_path).split(os.path.sep)[-3]
            except Exception:
                logger.error(
                    "Could not obtain unit from folder name \"{0}\": ".format(file_path), __file__)
                continue

            # set unit id
            familyObj.setUnitID(unit_id.upper())
            familyObj.fileName = file_name

            # get the unit from the folder name
            try:
                host = os.path.dirname(file_path).split(os.path.sep)[-2]
            except Exception:
                logger.error(
                    "Could not obtain host from folder name \"{0}\": ".format(file_path), __file__)
                continue

            f = None
            try:
                # Open file for reading
                f = open(file_path, 'r') if self.pre_replace is None else open(file_path, 'rb')
            except IOError:
                logger.error(
                    "Could not open sample file \"{0}\" in read mode: ".format(file_name), __file__)
                continue

            if self.pre_replace is not None:
                f = self.pre_replace_process(f.read())

            header = []

            for line in reader(f, delimiter=';'):

                if not line:
                    continue

                line = self.decode_func(line)

                # Get the first line as header and jumps to the next line
                if not header:
                    header = [item.upper() for item in line]
                    continue

                if len(header) != len(line):
                    logger.warning("Line with invalid number of fields in file '{0}'".format(familyObj.fileName))
                    continue

                try:
                    # Creates a dict from the zip between header and the current line
                    document = dict(zip(header, [(None if item == 'null' else item) for item in line]))
                    document["DATETIME"] = date
                    document["IP"] = host

                    try:
                        data_time = familyObj.parseEnvelopeDataTime(date)
                    except ValueError as e:
                        logger.warning("Could not build mediationEnvelope due to {0}: ".format(e), __file__)
                        continue

                    # Setting up the envelope
                    familyObj.addDocument({"dataTime": data_time, "granularitySec": 5, "data": document})
                    self.nextOp(familyObj=familyObj, baseObject=baseObject)
                    familyObj.clearDocuments()

                except Exception as e:
                    logger.warning(
                        "Unable to process {0} in unit {1} because wrong format => {2}".format(familyObj.fileName,
                                                                                               unit_id, e), __file__)
                    continue
