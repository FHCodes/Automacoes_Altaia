#!/usr/bin/env python

__doc__ = \
    '''
    Nokia OmeS XML parser

     Spec file syntax:
    <operation type="Readers" name="NOKIA.OMeS"/>
'''

__version__ = '2.0'

__authors__ = [
    "Version 0.1: Francisco Santiago <francisco-j-santiago@telecom.pt>"
    "Version 2.0: Joao Pio <joao-t-pio@telecom.pt>"
]

# Native libraries
import gzip
import re
import xml.etree.cElementTree as ET
import os
import time
import importlib

# Local libraries
BaseOperator = importlib.import_module("shelf.collectorprocess.operators.BaseOperator").BaseOperator
FamilyObject = importlib.import_module("shelf.collectorprocess.operators.FamilyObject").FamilyObject
logger = importlib.import_module("shelf.collectorprocess.logger").logger


class Operator(BaseOperator):

    # Class Constructor
    def __init__(self, operationParams, baseObject={}):
        BaseOperator.__init__(self, operationParams, baseObject=baseObject)
        self.MAX_DUPLICATE_WARNINGS = 100
        self.duplicateWarnings = 0

    @staticmethod
    def convert(familyObj=FamilyObject()):

        for document in familyObj.getDocuments():

            # removes the superfluous info from the timestamp and turns it into a time structure
            time_struct = time.strptime(document["data"]["STARTTIME"][:19], "%Y-%m-%dT%H:%M:%S")

            # depending on the interval, do the rounding
            minutes = time_struct.tm_min
            if document["data"]["INTERVAL"] == "15":
                if 0 <= minutes < 15:
                    document["data"]["STARTTIME"] = time.strftime("%Y-%m-%d %H:00:00", time_struct)
                elif 15 <= minutes < 30:
                    document["data"]["STARTTIME"] = time.strftime("%Y-%m-%d %H:15:00", time_struct)
                elif 30 <= minutes < 45:
                    document["data"]["STARTTIME"] = time.strftime("%Y-%m-%d %H:30:00", time_struct)
                elif 45 <= minutes < 60:
                    document["data"]["STARTTIME"] = time.strftime("%Y-%m-%d %H:45:00", time_struct)
            elif document["data"]["INTERVAL"] == "60":
                # rewrites the timestamp with the correct format while flooring the minutes and the seconds
                document["data"]["STARTTIME"] = time.strftime("%Y-%m-%d %H:00:00", time_struct)
            else:
                document["data"]["STARTTIME"] = time.strftime("%Y-%m-%d %H:%M:%S", time_struct)

    @staticmethod
    def getelements(filename_or_file, tag):
        context = iter(ET.iterparse(filename_or_file, events=('start', 'end')))
        # get root element
        _, root = next(context)

        namespace = None
        for event, elem in context:
            if event == 'start' and namespace is None:
                if "}" in elem.tag:
                    namespace = elem.tag.split("}")[0].strip("{")
                    namespace = "{" + namespace + "}"
                else:
                    namespace = ""

            if event == 'end' and elem.tag == namespace + tag:
                yield elem, namespace
                # preserve memory
                root.clear()

    def process(self, familyObj=FamilyObject(), baseObject={}):

        logger.debug("Reading NSN Performance XML files' contents...", __file__)
        files_to_process = familyObj.getFiles()
        familyObj.clearFiles()

        for filePath in files_to_process:

            dict_family_objs = dict()
            # Get file's name
            familyObj.fileName = os.path.basename(filePath).replace('.gz', '')

            # Compressed file
            if 'gz' in filePath:
                try:
                    # Open file for writing
                    f = gzip.open(filePath)
                except IOError:
                    logger.warning(
                        "Could not open sample file \"{}\" in read mode: ".format(
                            familyObj.fileName), __file__)
                    continue
            # Uncompressed file
            else:
                f = filePath

            # These will be the same for all measures found inside each <PMSetup> node.
            common_values_document = {
                "STARTTIME": "",
                "INTERVAL": "",
                "DISTNAME": ""
            }
            for pm_setup, namespace in self.getelements(f, "PMSetup"):

                # Parse the time of measurement in order for it to become in TIMESTAMP form
                common_values_document["STARTTIME"] = pm_setup.attrib["startTime"]
                common_values_document["INTERVAL"] = pm_setup.attrib["interval"]

                for pm_mo_result in list(pm_setup.getiterator(namespace + "PMMOResult")):
                    ################################## DNs ##################################
                    monitored_objs_list = list()
                    first_dn_processed = False
                    for mo in list(pm_mo_result.getiterator(namespace + "MO")):
                        for dn in list(mo.getiterator(namespace + "DN")):

                            # print "READER: DN: {0}".format(dn.text)
                            dn_val = dn.text

                            # Store first DN value to use later as co-relation key in enrichment
                            if not first_dn_processed:
                                first_dn_processed = True
                                common_values_document["DISTNAME"] = dn.text.strip()

                            dn_val = dn_val.strip()
                            dn_val = re.sub('PLMN-PLMN/|NSNNetwork-.*?/', '', dn_val)
                            dn_val = dn_val.replace("/-", ",")
                            dn_val = dn_val.replace("//", "\\")
                            dn_val = dn_val.replace(";", " ")
                            monitored_objs_list.append(dn_val)

                    monitored_objs_str = "/".join(monitored_objs_list)

                    ################################## PMTarget ##################################
                    for pm_target in list(pm_mo_result.getiterator(namespace + "PMTarget")):

                        if not pm_target.attrib["measurementType"]:
                            break

                        # Get measUnit ID from node attribute
                        unit_id = pm_target.attrib["measurementType"].upper()

                        if unit_id not in dict_family_objs:
                            new_family_object = FamilyObject()

                            new_family_object.fileName = familyObj.fileName

                            new_family_object.setUnitID(unit_id)

                            dict_family_objs[unit_id] = new_family_object

                        familyObj.clearDocuments()

                        document = {
                            "MEASUREDOBJECTID": monitored_objs_str
                        }

                        # Adds common values to new document
                        document.update(common_values_document)

                        # Get all columns and values for this measurement by iterating all children of <PMTarget>
                        for counter in [x for x in pm_target.getiterator() if x.tag != namespace + "PMTarget"]:
                            if "}" in counter.tag:
                                counter.tag = counter.tag.split("}")[1]

                            document[counter.tag.upper()] = counter.text.strip()

                        # Isolate each ID
                        for key, value in [(x.split("-",1)[0], x.split("-",1)[1]) for x in
                                           document["DISTNAME"].split("/")]:
                            if key.upper() == "PLMN": continue
                            if key.upper() == "NSNNETWORK": continue
                            document[key.upper()] = value

                        try:
                            data_time = dict_family_objs[unit_id].parseEnvelopeDataTime(common_values_document["STARTTIME"])
                            granularity_sec = dict_family_objs[unit_id].parseEnvelopeGranularitySec(
                                common_values_document["INTERVAL"])
                        except ValueError as e:
                            logger.warning(
                                "Could not build mediationEnvelope due to {0}: ".format(
                                    e), __file__)
                            continue

                        data_document = {"dataTime": data_time, "granularitySec": granularity_sec, "data": document}

                        dict_family_objs[unit_id].addDocument(data_document)

            for unit in dict_family_objs:
                self.convert(familyObj=dict_family_objs[unit])
                self.nextOp(familyObj=dict_family_objs[unit], baseObject=baseObject)
