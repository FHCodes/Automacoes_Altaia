#!/usr/bin/env python

__version__ = '1.0'

__doc__ = '''
    ITALTEL iMSC CORE Performance Softswitch XML Reader
'''

__authors__ = [
	"Version 1.0: paulo-a-gil <paulo-a-gil@alticelabs.com>"
]

import os
import importlib
from datetime import datetime
import xml.etree.ElementTree as ET

# Local libraries
BaseOperator = importlib.import_module("shelf.collectorprocess.operators.BaseOperator").BaseOperator
FamilyObject = importlib.import_module("shelf.collectorprocess.operators.FamilyObject").FamilyObject
logger = importlib.import_module("shelf.collectorprocess.logger").logger

# A very efficient function to check if a string value can be casted to int or float
# Takes a string as input
# Returs True or False
def is_numeric(value):
    try:
        int(value)
        return True
    except ValueError:
        try:
            float(value)
            return True
        except ValueError:
            return False

class Operator(BaseOperator):

    # Class constructor
    def __init__(self, operationParams, baseObject={}):
        BaseOperator.__init__(self, operationParams, baseObject=baseObject)

    def process(self, familyObj=FamilyObject(), baseObject={}):
        logger.debug("Reading ITALTEL iMSC CORE Performance XML file contents...", __file__)
        filePath = familyObj.getFiles()[0]

        familyObj.clearDocuments()

        fileName = os.path.basename(filePath)
        familyObj.fileName = fileName

        # If file is empty, 'bota fora' :)
        if os.path.getsize(filePath) == 0:
            logger.warning("File {0} is empty.".format(fileName), __file__)
            return

        # Try parsing file
        xmlRoot = None
        try:
            tree = ET.parse(filePath)
            xmlRoot = tree.getroot()
        except IOError:
            logger.error("Could not open sample file \"{0}\" in read mode: ".format(fileName), __file__)

        try:
            # Initializing head variable
            head = dict()

            # Loop through root level
            for rootElement in xmlRoot:
                # In the root level we get EDITION and INTERVAL tags
                if rootElement.tag == 'EDITION':
                    head['EDITION'] = rootElement.text
                elif rootElement.tag == 'INTERVAL':
                    # Get BEGINTIME and ENDTIME
                    beginTime = "{0} {1}".format(rootElement.get('BeginDate'), rootElement.get('BeginTime'))
                    head['BEGINTIME'] = datetime.strptime(beginTime, "%d/%m/%Y %H-%M-%S")
                    head['BEGINTIME'] = datetime.strftime(head['BEGINTIME'], "%Y-%m-%d %H:%M:%S")
                    endTime = "{0} {1}".format(rootElement.get('EndDate'), rootElement.get('EndTime'))
                    head['ENDTIME'] = datetime.strptime(endTime, "%d/%m/%Y %H-%M-%S")
                    head['ENDTIME'] = datetime.strftime(head['ENDTIME'], "%Y-%m-%d %H:%M:%S")
                    # GRANULARITYPERIOD is 10 minutes (according to SOW)
                    head['GRANULARITYPERIOD'] = 10

                    # Loop through second level (Switch Level)
                    for switchElement in rootElement:
                        head['GATEWAY'] = switchElement.get('id')

                        # Loop through third level (Unit Level)
                        for unitElement in switchElement:
                            familyObj.setUnitID(unitElement.tag)

                            # Loop through fourth level (Measurement Level)
                            for measElement in unitElement:
                                # Create empty document with head values
                                document = dict(head)
                                # Get OBJECTID value
                                document['OBJECTID'] = measElement.get('id')

                                # If OBJECTID field is None, set it to empty instead so it can produce an event
                                if document['OBJECTID'] == None:
                                    document['OBJECTID'] = ''

				                # If a counter can't be parsed as int or float, the document cannot be sent
                                parseDocument = True

                                # Count the number of counters present in the sample for the measurement
                                nCounters = 0

                                # Loop through fifth level (Counter/Struct Level)
                                for counterElement in measElement:
                                    nCounters = nCounters + 1

                                    # Checks if is counter or struct
                                    if counterElement.getchildren() == []:
                                        # Checks if the content of the counter element is int or float
                                        # If it is not a number, break and jump to the next measElement
                                        if not is_numeric(counterElement.text):
                                            parseDocument = False
                                            break

                                        document[counterElement.tag.upper()] = counterElement.text

                                    else:
                                        # Loop through all elements in struct
                                        nCounters = nCounters - 1
                                        for structElement in counterElement:
                                            nCounters = nCounters + 1
                                            document['{0}_{1}'.format(counterElement.tag.upper(), structElement.tag.upper())] = structElement.text

                                if nCounters == 0:
                                    if not is_numeric(measElement.text):
                                        parseDocument = False

                                    document[measElement.tag.upper()] = measElement.text

                                if parseDocument:
                                    # Parse envelope DataTime
                                    try:
                                        timestamp = familyObj.parseEnvelopeDataTime(document["BEGINTIME"])
                                    except ValueError as e:
                                        logger.warning("Could not build mediationEnvelope due to {0}: ".format(e), __file__)
                                        continue

                                    # Setting up the envelope
                                    familyObj.addDocument({"dataTime": timestamp, "granularitySec": 600, "data": document})
                                    self.nextOp(familyObj=familyObj, baseObject=baseObject)

                                # Clear documents from familyObj
                                familyObj.clearDocuments()
        except Exception as e:
            logger.warning("Unable to process {0} due to {1}: ".format(familyObj.fileName, e), __file__)
