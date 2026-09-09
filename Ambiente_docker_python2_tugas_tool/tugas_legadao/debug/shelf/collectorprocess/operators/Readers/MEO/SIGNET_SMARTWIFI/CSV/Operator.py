#!/usr/bin/env python

__doc__ = \
    '''
    Enrichment Operator
'''

__version__ = '0.2'

__authors__ = [
    "Version 0.1: Pedro Silva <pedro-s-silva@alticelabs.com>"
    "Version 0.2: Paulo Gil <paulo-a-gil@alticelabs.com>"
]

import csv
import importlib
import os
import re
from subprocess import call
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
        logger.debug("Reading MEO SIGNET CLIENT ENRICH SMARTWIFI CSV file contents...", __file__)
        filesToProcess = familyObj.getFiles()

        for filePath in filesToProcess:
            familyObj.clearDocuments()
            originalFilePath = filePath

            # sacar nome do ficheiro sem o path
            fileName = os.path.basename(originalFilePath)
            familyObj.fileName = fileName

            # Flag to indicate if we need to remove file at the end of each parsed file
            removeFile = False

            # Try gunzip the file
            try:
                # Open file for writing
                if os.path.splitext(originalFilePath)[1] == ".zip":
                    removeFile = True
                    # Create a hidden, temporary file name without the .zip extension
                    fileDir = os.path.dirname(originalFilePath)
                    fileName = "." + os.path.basename(originalFilePath)
                    fileName = os.path.splitext(fileName)[0]
                    filePath = os.path.join(fileDir, fileName)

                    fOut = open(filePath, "w")
                    call(["gunzip", "-c", originalFilePath], stdout=fOut)

                    fOut.close()

                    if os.path.exists(filePath) == True:
                        if os.path.getsize(filePath) == 0:
                            os.remove(filePath)
                            raise IOError("")
                    else:
                        logger.warning("Could not create a hidden file \"{}\" in read mode: ".format(filePath))
                        continue
            except IOError:
                logger.warning("Could not open sample file \"{}\" in read mode: ".format(filePath), __file__)
                continue

            # If file is empty, bota fora :)
            if os.path.getsize(filePath) == 0:
                logger.warning("File {0} is empty.".format(fileName), __file__)
                continue

            # Try opening the file
            try:
                f = open(filePath, "r")
            except IOError:
                logger.error("Could not open file \"{0}\" in read mode.".format(fileName), __file__)

            # sacar data do nome do ficheiro
            familyObj.setUnitID(re.sub(r"\.(DIVISOES_ADMINISTRATIVAS)_.*$", r"\1", fileName).upper())
            regex = re.search(r'^\.DIVISOES_ADMINISTRATIVAS\_.*(?P<startTime>\d{14}).*$', fileName)
            startTime = (datetime.strptime(regex.group('startTime'), "%Y%m%d%H%M%S")).strftime('%Y-%m-%d %H:%M:%S')

            try:
                data_time = familyObj.parseEnvelopeDataTime(startTime)
            except ValueError as e:
                logger.warning("Could not build mediationEnvelope due to {0}: ".format(e), __file__)
                continue

            try:
                for line in csv.DictReader(f, delimiter=";"):
                    document = {key:value.decode("latin-1") for key, value in line.iteritems()}
                    document['DATETIME'] = startTime
                    document['GRANULARITYPERIOD'] = 1440

                    # envelope
                    familyObj.addDocument({"dataTime": data_time, "granularitySec": 1440, "data": document})
                    self.nextOp(familyObj=familyObj, baseObject=baseObject)
                    familyObj.clearDocuments()

            except Exception as e:
                logger.warning("ERROR: {0} in file {2}".format(e, fileName))

            # Remove gunzipped file from filesystem
            if removeFile:
                os.remove(filePath)
