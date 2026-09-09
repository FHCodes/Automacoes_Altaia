#!/usr/bin/env python

__doc__ = \
    '''
    NOKIA NSP MPLS CountInstance reader
'''

__version__ = '1.0'
__authors__ = [
    "Version 1.0: Joao Pio <joao-t-pio@alticelabs.com>"
]

# Native libraries
import re
import os
from datetime import datetime
import importlib

# Local libraries
BaseOperator = importlib.import_module("shelf.collectorprocess.operators.BaseOperator").BaseOperator
FamilyObject = importlib.import_module("shelf.collectorprocess.operators.FamilyObject").FamilyObject
logger = importlib.import_module("shelf.collectorprocess.logger").logger


class Operator(BaseOperator):

    # Class Constructor
    def __init__(self, operationParams, baseObject={}):
        BaseOperator.__init__(self, operationParams, baseObject=baseObject)

    def process(self, familyObj=FamilyObject(), baseObject={}):

        files_to_process = familyObj.getFiles()
        familyObj.clearDocuments()

        logger.debug("Reading NOKIA NSP CountInstance XML files' contents...", __file__)

        for file_path in files_to_process:
            logger.debug("Processing file '{0}'".format(file_path), __file__)

            file_name = os.path.basename(file_path)
            familyObj.fileName = file_name
            document = dict()

            unit_match = re.match("^(.*?)_(.*?)_(.*?)_(.*?)\.xml", file_name)
            document["GRANULARITYPRD"] = os.path.getctime(file_path)

            if unit_match is not None:
                document["MONITOREDOBJECTSITENAME"] = unit_match.group(4)
                document["MONITOREDOBJECTSITEID"] = unit_match.group(3)
                familyObj.unitID = unit_match.group(1).upper()
            else:
                logger.warning("Couldn't get unit ID in file: {0}".format(file_name), __file__)
                continue

            try:
                f = open(file_path, 'r')
            except IOError:
                logger.warning("Could not open sample file \"{0}\" in read mode: ".format(file_name), __file__)
                continue

            for line in f.readlines():

                if not line:
                    continue
                elif "<result>" in line:
                    document["RESULT"] = int(line.split("</result>")[0].split("<result>")[1])
                elif "<responseTime>" in line:
                    str_date = line.split("</responseTime>")[0].split("<responseTime>")[1]
                    # ex: Apr 20, 2017 6:29:35 PM
                    date_in = datetime.strptime(str_date, '%b %d, %Y %I:%M:%S %p')
                    date_out = datetime.strftime(date_in, '%Y-%m-%d %H:%M:%S')
                    document["COLLECTTIME"] = date_out

            # Prepare the document for NAMF consumption
            try:
                # Parse the date
                data_time = familyObj.parseEnvelopeDataTime(document["COLLECTTIME"])
                # no granularity period available, just create one
                granularity_sec = "60"
            except ValueError as e:
                logger.error(
                    "Could not build mediationEnvelope due to {0}: ".format(e), __file__)
                continue
            except KeyError as e:
                logger.error(
                    "Could not build mediationEnvelope due to {0}: ".format(e), __file__)

            familyObj.addDocument(
                {"dataTime": data_time, "granularitySec": granularity_sec, "data": document})
            self.nextOp(familyObj=familyObj, baseObject=baseObject)
            familyObj.clearDocuments()
