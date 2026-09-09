#!/usr/bin/env python

__doc__ = \
    '''
    Enrichment Operator
'''

__version__ = '0.1'

__authors__ = [
    "Version 0.1: Pedro Silva <pedro-c-silva@alticelabs.com>"
]

# import vendorConvert
from csv import reader
import csv
import importlib
import os
import re
from datetime import datetime

# Local libraries
BaseOperator = importlib.import_module("shelf.collectorprocess.operators.BaseOperator").BaseOperator
FamilyObject = importlib.import_module("shelf.collectorprocess.operators.FamilyObject").FamilyObject
logger = importlib.import_module("shelf.collectorprocess.logger").logger


class Operator(BaseOperator):

    # Class Constructor
    def __init__(self, operationParams, baseObject={}):
        BaseOperator.__init__(self, operationParams, baseObject=baseObject)

    def process(self, familyObj=FamilyObject(), baseObject={}):
        filesToProcess = familyObj.getFiles()
        familyObj.clearDocuments()

        for file_path in filesToProcess:

            # Get file's name
            file_name = os.path.basename(file_path)
            familyObj.fileName = file_name

            try:
                f = open(file_path, 'r')
            except IOError:
                logger.warning("Could not open sample file '{}' in read mode: ".format(file_name))
                continue

            column_names = []
            header_start = False
            header_end = False
            n_line = 0
            granularity_min = None
            try:
                for line in reader(f, delimiter=","):
                    if line == '\n' or len(line) < 1:
                        continue

                    if "File Name" in line[0]:
                        header_start = True
                        # family name # Exported Object: SBC7KAclOffListIntStats
                        # with granularity
                        familia = re.search(r"^(?P<unitID>\S+?)\-\d+\-\d+\-\d+\-\d+\-\d+\-(?P<granularity>\d+)MIN.*", line[1])
                        if familia is not None:
                            try:
                                familyObj.setUnitID(familia.group("unitID").upper())
                                granularity_min = int(familia.group("granularity"))
                            except ValueError:
                                logger.warning("Could not convert granularity from 'File Name': {0}".format(familyObj.fileName))
                        else:
                            # without granularity
                            familia = re.search(r"^(?P<unitID>\S+?)\-\d+\-\d+\-\d+\-\d+\-\d+.*", line[1])
                            familyObj.setUnitID(familia.group("unitID").upper())
                        continue

                    if "NODE_ID" in line[0] and header_end == False:
                        header_end = True

                    if header_start == True and header_end == False:
                        continue

                    if header_start == True and header_end == True and len(column_names) == 0:
                        line[0] = line[0][1:]
                        column_names = line
                        continue

                    n_line += 1

                    if len(line) != len(column_names):
                        logger.warning("Number of values in line {0} is different than number of announced columns in sample '{1}'".format(n_line,familyObj.fileName))
                        continue

                    # strip espacos header
                    # column_names=str(column_names).upper()
                    res = []
                    for i in column_names:
                        # j = i.replace(' ', '')
                        res.append(i.upper())

                    document = dict(zip(res, line))

                    try:
                        # Convert timestamp
                        document['TIMESTAMP'] = datetime.strptime(document['TIMESTAMP'], "%Y/%m/%d %H:%M:%S")
                        document['TIMESTAMP'] = datetime.strftime(document['TIMESTAMP'], "%Y-%m-%d %H:%M:%S")
                        data_time = familyObj.parseEnvelopeDataTime(document["TIMESTAMP"])
                    except ValueError as e:
                        logger.warning("Could not build mediationEnvelope due to {0}: ".format(e), __file__)
                        continue

                    if granularity_min is not None:
                        document['GRANULARITYPERIOD'] = granularity_min
                    else:
                        document['GRANULARITYPERIOD'] = 5

                    # envelope
                    familyObj.addDocument({"dataTime": data_time, "granularitySec": int(document["GRANULARITYPERIOD"]), "data": document})
                    self.nextOp(familyObj=familyObj, baseObject=baseObject)
                    familyObj.clearDocuments()

            except csv.Error as e:
                logger.warning("{0} in line {1} of file {2}".format(e, n_line, file_name))