#!/usr/bin/env python

__doc__ = \
    '''
    Enrichment Operator
'''

__version__ = '0.1'

__authors__ = [
    "Version 0.1: Pedro Silva <pedro-s-silva@alticelabs.com>"
]

# import vendorConvert
import gzip
from csv import reader
import csv
import importlib
import os
import re
import io
from datetime import datetime

# Local libraries
BaseOperator = importlib.import_module("shelf.collectorprocess.operators.BaseOperator").BaseOperator
FamilyObject = importlib.import_module("shelf.collectorprocess.operators.FamilyObject").FamilyObject
logger = importlib.import_module("shelf.collectorprocess.logger").logger


class Operator(BaseOperator):

    # Class Constructor
    def __init__(self, operationParams, baseObject={}):
        BaseOperator.__init__(self, operationParams, baseObject=baseObject)

        self.filename_regex = re.compile('^(?P<unit_id>[^\d]+?)\_(?:day\_)*(?P<start_time>\d{8})\_.*\.csv.*')
        self._polls = dict()
        self._lastReportedTimestamp = ""

    def process(self, familyObj=FamilyObject(), baseObject={}):
        filesToProcess = familyObj.getFiles()
        familyObj.clearDocuments()

        for file_path in filesToProcess:

            # Get file's name
            file_name = os.path.basename(file_path)
            familyObj.fileName = file_name

            try:
                # Open file for writing
                if os.path.splitext(file_name)[1] == ".gz":
                    f = io.BufferedReader(gzip.open(file_path))
                else:
                    f = open(file_path, 'r')
            except IOError:
                logger.warning("Could not open sample file '{0}' in read mode: ".format(file_name))
                continue

            filename_match = self.filename_regex.match(file_name)

            if filename_match is not None:
                unit_id = filename_match.group("unit_id")
                start_time = (datetime.strptime(filename_match.group('start_time'), "%Y%m%d")).strftime('%Y-%m-%d 00:00:00')
            else:
                logger.warning("Could not recognize unit id of file '{0}': ".format(file_name))
                continue

            familyObj.unitID = unit_id.upper()

            column_names = None
            n_column_names = None
            key = ['VENDOR','MODEL','TYPE','SUP_24G','SUP_5G','SUP_11_AC','SUP_11_AX','SUP_11_N','SUP_11_V', 'SUP_6G', 'FINGERPRINT_MODEL',
                   'FINGERPRINT_TYPE', 'FINGERPRINT_PLATFORM', 'FINGERPRINT_OS', 'FINGERPRINT_IS_IOT', 'FINGERPRINT_AV_DETECTED']

            n_line = 0
            try:

                for line in reader(f, delimiter=","):

                    n_line += 1

                    if n_line == 1:

                        n_column_names = len(line)
                        # Fix name of first element of row that has a # character attached
                        if n_column_names > 0:

                            # Store column names into a list
                            column_names = [name.upper() for name in line]
                        else:
                            logger.warning(
                                "Could not retrieve column names from first row of sample '{0}'".format(file_name))
                            break

                    else:
                        if len(line) == n_column_names:

                            document = dict(zip(column_names, line))
                            document['UTC_TIMESTAMP'] = start_time
                            if familyObj.unitID == 'CLIENT_ANALYSIS':
                                hashkey = ''
                                for i in key:
                                    if i in document.keys() and document[i]:
                                        if document[i] != '':
                                            hashkey = hashkey + ',' + i + ':' + document[i]

                                document['HASHKEY'] = hashkey.strip(',')

                            try:
                                data_time = familyObj.parseEnvelopeDataTime(document["UTC_TIMESTAMP"])
                            except ValueError as e:
                                logger.warning("Could not build mediationEnvelope due to {0}: ".format(e), __file__)
                                continue

                            document['DURATION'] = 1440
                            # envelope
                            familyObj.addDocument({"dataTime": data_time, "granularitySec": 86400, "data": document})
                            self.nextOp(familyObj=familyObj, baseObject=baseObject)
                            familyObj.clearDocuments()
                        else:
                            logger.warning(
                                "Number of values in line {0} is different than number of announced columns in sample '{1}'".format(
                                    n_line, file_name))

            except csv.Error as e:
                logger.warning("{0} in line {1} of file {2}".format(e, n_line, file_name))
