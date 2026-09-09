#!/usr/bin/env python

__doc__ = \
    '''Ericsson .data ASN1 CSV reader'''

__version__ = '1.0'

__authors__ = ["Version 1.0: Joao Pio <joao-t-pio@alticelabs.com>"]

import re
from csv import reader
import os
import importlib
from datetime import datetime, timedelta

# Local libraries
BaseOperator = importlib.import_module("shelf.collectorprocess.operators.BaseOperator").BaseOperator
FamilyObject = importlib.import_module("shelf.collectorprocess.operators.FamilyObject").FamilyObject
logger = importlib.import_module("shelf.collectorprocess.logger").logger


class Operator(BaseOperator):

    # Class Constructor
    def __init__(self, operationParams, baseObject={}):
        BaseOperator.__init__(self, operationParams, baseObject=baseObject)

        self.filename_regex = re.compile("^ERICSSON_CORE_HLR_(?P<nename>[^_]+?)_(?P<unit_id>[^_]+?)_(?P<date>\d+)\.csv$")

    def process(self, familyObj=FamilyObject(), baseObject={}):

        files_to_process = familyObj.getFiles()

        logger.debug("Reading Ericsson HLR CSV files' contents...", __file__)

        for filePath in files_to_process:

            familyObj.clearDocuments()

            # Get file's name to find the unitID
            file_name = os.path.basename(filePath)

            file_match = self.filename_regex.match(file_name)

            if file_match is not None:
                unit_id = file_match.group('unit_id')
            else:
                logger.warning("Could not obtain unit ID from sample name {0}".format(file_name), __file__)
                continue

            familyObj.setUnitID(unit_id)
            familyObj.fileName = file_name
            familyObj.clearDocuments()

            try:
                # Open file for writing
                f = open(filePath, 'r')
            except IOError:
                logger.error(
                    "Could not open sample file \"{0}\" in read mode: ".format(file_name), __file__)
                continue

            # Used to store the column names from the first line of each file
            column_names_list = None
            n_column_names = 0

            n_line = 0
            for line in reader(f, delimiter=';', quotechar='"'):
                n_line += 1

                # Collects column names from first line of file
                if n_line == 1:
                    if len(line) == 0:
                        logger.warning(
                            "No column names found in first line of file \"{0}\"".format(file_name), __file__)
                        break

                    column_names_list = [x.upper() for x in line]
                    n_column_names = len(column_names_list)
                    continue

                # Checks if number of values in row is the same as the announced columns in the first line
                if len(line) != n_column_names:
                    logger.warning(
                        "Number of values in line {0} is different than number of announced columns in sample \"{1}\"".format(
                            n_line, file_name), __file__)
                    continue

                # Build the document
                document = dict(zip(column_names_list, line))

                # Clean empty columns (no header name)
                try:
                    document.pop("", None)
                except KeyError:
                    # No empty key
                    pass

                meas_end_time = datetime.strptime(document["MEASENDTIME"], '%Y-%m-%d %H:%M:%S')
                meas_start_time = datetime.strptime(document["MEASSTARTTIME"], '%Y-%m-%d %H:%M:%S')
                granularity = meas_end_time - meas_start_time
                document["GRANULARITYPERIOD"] = granularity.seconds

                try:
                    try:
                        data_time = familyObj.parseEnvelopeDataTime(document["MEASSTARTTIME"])
                        granularity_sec = familyObj.parseEnvelopeGranularitySec(granularity.seconds)
                    except ValueError as e:
                        logger.warning("Could not build mediationEnvelope due to {0}: ".format(e), __file__)
                        continue

                    familyObj.addDocument({"dataTime": data_time, "granularitySec": granularity_sec, "data": document})
                except Exception, e:
                    logger.warning(
                        "Unable to process {0} in unit {1} because wrong format => {2}".format(familyObj.fileName,
                                                                                               unit_id, e), __file__)
                    continue

            self.nextOp(familyObj=familyObj, baseObject=baseObject)
