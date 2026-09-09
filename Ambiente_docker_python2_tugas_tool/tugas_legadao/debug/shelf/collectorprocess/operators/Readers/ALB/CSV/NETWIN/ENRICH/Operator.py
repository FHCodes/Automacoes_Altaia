#!/usr/bin/env python

__doc__ = \
    '''
    ALB NETWIN ENRICH CSV files reader
'''

__version__ = '1.0'

__authors__ = [
    "Version 0.1: Joao Pio <joao-t-pio@alticelabs.com>"
]

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

        self.filename_regex = re.compile(r'^(?P<unit>.+)_(?P<date>[^_]+).csv$')

    def process(self, familyObj=FamilyObject(), baseObject={}):

        logger.debug("Reading ALB NETWIN ENRICH CSV file contents...", __file__)
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

            unit_id = file_name_match.group("unit")

            # ALTAIA_CADASTRO_PARQUE_ONT is too big and doesnt have latin characters. For performance reasons, decoding is not feasible
            if unit_id.upper() == "ALTAIA_CADASTRO_PARQUE_ONT":
                decode = False
            else:
                decode = True

            date = file_name_match.group("date").split('.')[0].strip()

            # Parse and change datetime format

            try:
                date = datetime.strptime(date, "%Y%m%d")
                date = datetime.strftime(date, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                date = None

            # set unit id
            familyObj.setUnitID(unit_id.upper())
            familyObj.fileName = file_name

            grouping = 30

            f = None
            try:
                # Open file for reading
                f = open(file_path, 'r')
            except IOError:
                logger.error(
                    "Could not open sample file \"{0}\" in read mode: ".format(file_name), __file__)
                continue

            header = []

            for line_index, line in enumerate(reader(f, delimiter=';')):

                if not line:
                    continue

                if decode:
                    line = [item.decode("latin-1") for item in line]

                # Get the first line as header and jumps to the next line
                if not header:
                    header = [item.upper() for item in line]
                    continue

                if len(header) != len(line):
                    logger.warning("Line with invalid number of fields in file '{0}'".format(familyObj.fileName))
                    continue

                try:
                    for index, l in enumerate(line):
                        if l == "null":
                            line[index] = ""

                    # Creates a dict from the zip between header and the current line
                    document = dict(zip(header, line))

                    # Filename did not provide the date
                    if date is None:
                        try:
                            date = datetime.strptime(document["DATA_EMISSAO"], "%Y%m%d")
                            date = datetime.strftime(date, "%Y-%m-%d %H:%M:%S")
                        except ValueError:
                            date = datetime.strptime(document["DATA_EMISSAO"], "%d/%m/%Y %H:%M:%S")
                            date = datetime.strftime(date, "%Y-%m-%d %H:%M:%S")

                    document["DATA_EMISSAO"] = date

                    try:
                        data_time = familyObj.parseEnvelopeDataTime(date)
                    except ValueError as e:
                        logger.warning("Could not build mediationEnvelope due to {0}: ".format(e), __file__)
                        continue

                    # Setting up the envelop
                    familyObj.addDocument({"dataTime": data_time, "granularitySec": 1440, "data": document})
                    if line_index % grouping == 0:
                        self.nextOp(familyObj=familyObj, baseObject=baseObject)
                        familyObj.clearDocuments()

                except Exception as e:
                    logger.warning(
                        "Unable to process {0} in unit {1} because wrong format => {2}".format(familyObj.fileName,
                                                                                               unit_id, e), __file__)
                    continue

            # Flush the remaining events
            self.nextOp(familyObj=familyObj, baseObject=baseObject)
            familyObj.clearDocuments()