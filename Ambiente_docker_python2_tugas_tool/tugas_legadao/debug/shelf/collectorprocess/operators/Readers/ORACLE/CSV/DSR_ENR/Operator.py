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
import gzip
from csv import reader
import csv
import importlib
import os
import re
import io
import sys
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

            #regex = re.search(r'soam_dsr\S+\_.*(?P<startTime>\d{6}\-\d{4}).*_(?P<unitID>\S+RouteRule.*)\.csv.*',fileName)
            regex = re.search(r'soam_(?P<serverId>dsr\S+)\_.*\d{6}\-\d{4}.*_\S+RouteRule.*\.csv.*',file_name)
            # startTime = '{0}'.format(regex.group('startTime'))
            # startTime = datetime.strftime(startTime, "%Y%m%d%H%M%S")
            # startTime = (datetime.strptime(regex.group('startTime'), "%m%d%y-%H%M")).strftime('%Y-%m-%d %H:%M:00')

            column_names = []
            header_start = False
            header_end = False
            n_line = 0
            try:
                for line in reader(f, delimiter=","):
                    if "###" in line[0] and header_start==False:
                        header_start = True
                        continue

                    if "###" in line[0] and header_end==False:
                        header_end = True
                        continue

                    if "Date/Time Generated" in line[0]:
                        #TBD sacar a data # Date/Time Generated: 2022-Apr-06 06:00:21 Europe/Lisbon
                        timestamp = re.search(r".*\s+Date\/Time Generated\:\s+(?P<startTime>\d{4}\-\w{3}\-\d{2}\s+\d{2}\:\d{2}\:\d{2})\s.*",line[0])
                        startTime = datetime.strptime(timestamp.group("startTime"), "%Y-%b-%d %H:%M:%S")
                        startTime = datetime.strftime(startTime, "%Y-%m-%d %H:%M:%S")
                        continue

                    if "Exported Object" in line[0]:
                        #TBD sacar o nome da familia # Exported Object: PeerRouteRule
                        #familia = re.search(r".*Exported\s+Object\:\s+(?P<unitID>.*)$",line[0])
                        familia = re.search(r".*Exported\s+Object\:\s+(?P<unitID>\S+RouteRule)$",line[0])
                        familyObj.setUnitID(familia.group("unitID"))
                        continue

                    if header_end==False:
                        continue

                    if header_start == True and header_end == True and column_names==[]:
                        line[0]=line[0][1:]
                        column_names=line
                        continue

                    n_line += 1

                    if len(line) != len(column_names):
                        logger.warning(
                            "Number of values in line {0} is different than number of announced columns in sample '{1}'".format(n_line, familyObj.fileName))
                        continue

                    #strip espacos header
                    #column_names=str(column_names).upper()
                    res = []
                    for i in column_names:
                        #j = i.replace(' ', '')
                        res.append(i.upper())

                    document = dict(zip(res, line))
                    document['DATETIME'] = startTime
                    document['GRANULARITYPERIOD'] = 1440
                    document['SERVERID'] = regex.group('serverId')

                    try:
                        data_time = familyObj.parseEnvelopeDataTime(document['DATETIME'])
                    except ValueError as e:
                        logger.warning("Could not build mediationEnvelope due to {0}: ".format(e), __file__)
                        continue

                    # envelope
                    familyObj.addDocument({"dataTime": data_time, "granularitySec": int(document["GRANULARITYPERIOD"]) * 60, "data": document})
                    self.nextOp(familyObj=familyObj, baseObject=baseObject)
                    familyObj.clearDocuments()

            except csv.Error as e:
                logger.warning("{0} in line {1} of file {2}".format(e, n_line, file_name))
