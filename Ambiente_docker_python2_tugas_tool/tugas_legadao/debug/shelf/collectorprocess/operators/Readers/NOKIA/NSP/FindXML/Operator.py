#!/usr/bin/env python

__doc__ = \
    '''
    findResponse SOAP Reader.
'''

__version__ = '0.1'

__authors__ = [
    "Version 0.1: Francisco Santiago <francisco-j-santiago@telecom.pt>",
    "Version 1.0: Joao Pio <joao-t-pio@alticelabs.com>"
]

# Native libraries
import xml.etree.cElementTree as ET
import re
import os
import time
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

    @staticmethod
    def convert(family_obj=FamilyObject()):

        for document in family_obj.getDocuments():

            try:
                # Time was is either 20181115 (from filename) or Nov 15, 2018 11:10:38 PM (from responseTime node)
                match = re.match("^(?P<YEAR>19|20[0-9]{2})(?P<MONTH>1[0-2]|0[1-9])(?P<DAY>3[0-1]|0[1-9]|[1-2][0-9])$",
                                 document["data"]["DATETIME"])

                if match is None:
                    match = re.match(
                        "^(?P<MONTH>Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) (?P<DAY>3[0-1]|0[1-9]|[1-9]|[1-2][0-9]), (?P<YEAR>19|20[0-9]{2}) (?P<HOUR>1[0-2]|[1-9]):(?P<MIN>[0-5][0-9]|[0-9]):(?P<SEC>[0-5][0-9]|[0-9]) (?P<HFORMAT>AM|PM)$",
                        document["data"]["DATETIME"])
                else:
                    time_struct = datetime(int(match.group("YEAR")),
                                           int(match.group("MONTH")),
                                           int(match.group("DAY")))

                if match is None:
                    raise ValueError
                else:
                    if match.group("HFORMAT") == "AM":
                        corrected_hour = int(match.group("HOUR")) % 12
                    else:
                        corrected_hour = 12 + (int(match.group("HOUR")) % 12)

                    time_struct = datetime(int(match.group("YEAR")),
                                           int(family_obj._dateTranslationDict["MONTH"][match.group("MONTH")]),
                                           int(match.group("DAY")),
                                           corrected_hour,
                                           int(match.group("MIN")),
                                           int(match.group("SEC")))

                document["data"]["DATETIME"] = time.strftime("%Y-%m-%d %H:%M:%S", time_struct.timetuple())

            except KeyError:
                logger.error("Can't convert DATETIME since it's missing from the document", __file__)
                continue
            except ValueError:
                logger.error(
                    "Can't convert DATETIME due to unrecognized format {0}".format(document["data"]["DATETIME"]),
                    __file__)
                continue

    @staticmethod
    def get_elements(filename_or_file, tag):

        context = iter(ET.iterparse(filename_or_file, events=('start', 'end', 'start-ns', 'end-ns')))
        namespace = tuple()

        for event, elem in context:
            # Start of a namespace
            if event == 'start-ns':
                namespace = (elem[0], elem[1])

            # End of a namespace
            elif event == 'end-ns':
                namespace = tuple()

            # Start of a XML node
            elif event == 'start':
                pass

            # End of a XML node
            elif event == 'end' and len(namespace) != 0:
                if elem.tag == "{{{0}}}{1}".format(namespace[1], tag):
                    yield elem, namespace
                    # preserve memory
                    elem.clear()

        # Rewind in case it is a file type
        if isinstance(filename_or_file, file):
            filename_or_file.rewind()

    def process(self, familyObj=FamilyObject(), baseObject={}):

        files_to_process = familyObj.getFiles()
        familyObj.clearDocuments()

        logger.debug("Reading ALU SAM-O XML files' contents...", __file__)

        for file_path in files_to_process:

            logger.debug("Processing '{0}'".format(file_path), __file__)

            familyObj.fileName = os.path.basename(file_path)

            # Get possible information from the filename
            unit_match = re.match("disc_(.*?)_(.*?)\.xml", familyObj.fileName)

            if unit_match is not None:
                unit_id = unit_match.group(1)
                filename_date = unit_match.group(2)

                # Set the unit ID from the filename. Will be confirmed with the file's contents
                familyObj.setUnitID(unit_id)
            else:
                logger.warning("Couldn't get unit ID from filename: {0}".format(familyObj.fileName),
                               __file__)
                # Consider the possibility of unit identification being done inside the file, under the result node
                continue

            # Gets the begin time and element type from the file header if it exists
            for header_node, namespace in self.get_elements(file_path, "header"):
                try:
                    response_time = header_node.find("{{{0}}}responseTime".format(namespace[1]))
                    response_time = response_time.text
                except AttributeError:
                    response_time = filename_date
                    logger.warning("Could not get responseTime from file content, relying on the filename.", __file__)

            # Each result node could be a different family, so needs a different family object
            for result_node, namespace in self.get_elements(file_path, "result"):

                text_namespace = '{' + namespace[1] + '}'

                # Clear any previous documents
                familyObj.clearDocuments()

                # Find all the nodes of the family announced in the filename
                family_nodes = result_node.findall("{0}{1}".format(text_namespace, unit_id))

                if len(family_nodes) == 0:
                    logger.error("File {0} does not contain the expected family {1} in its contents. Skipping."
                                 .format(familyObj.fileName, unit_id), __file__)

                    self.nextOp(familyObj=familyObj, baseObject=baseObject)
                else:
                    # Loop all family nodes
                    for family_node in family_nodes:

                        # Start a new document and insert the response time
                        document = dict()
                        document["DATETIME"] = response_time

                        # Loop all the counters and ids in each family
                        for item in family_node.findall("*"):
                            # Get the item text and remove the namespace from the tag
                            if item.text:
                                document[item.tag.replace(text_namespace, "").upper()] = item.text.strip()
                            else:
                                document[item.tag.replace(text_namespace, "").upper()] = ""

                        # Prepare the document for NAMF consumption
                        try:
                            # Parse the date
                            data_time = familyObj.parseEnvelopeDataTime(response_time)
                            # no granularity period available, just create one
                            granularity_sec = str(60*60)
                        except ValueError as e:
                            logger.error(
                                "Could not build mediationEnvelope due to {0}: ".format(
                                    e), __file__)
                            continue

                        familyObj.addDocument(
                            {"dataTime": data_time, "granularitySec": granularity_sec, "data": document})

                # Final operations to the fields with timestamp and granularity period
                self.convert(family_obj=familyObj)

                self.nextOp(familyObj=familyObj, baseObject=baseObject)
