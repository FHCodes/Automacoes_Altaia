#!/usr/bin/env python

__doc__ = \
    '''CISCO PCRF CSV reader'''

__version__ = '1.0'

__authors__ = ["Version 1.0: Joao Pio <joao-t-pio@alticelabs.com>"]

import re
from csv import reader
import os
import importlib
from datetime import datetime as DT

# Local libraries
BaseOperator = importlib.import_module("shelf.collectorprocess.operators.BaseOperator").BaseOperator
FamilyObject = importlib.import_module("shelf.collectorprocess.operators.FamilyObject").FamilyObject
logger = importlib.import_module("shelf.collectorprocess.logger").logger


class Operator(BaseOperator):

    # Class Constructor
    def __init__(self, operationParams, baseObject={}):
        BaseOperator.__init__(self, operationParams, baseObject=baseObject)

        self.filename_regex = re.compile("^bulk-(?P<node>[^-]+?)-.*-(?P<source>[^-]+?)-(?P<date>\d+)\.csv$")
        self.counter_regex = re.compile("^(?P<unit_id>[^\.]+?)\..+$")

        self.units_regexes = {
            "COLLECTD": re.compile("^.*$"),
            "CPU": re.compile("^cpu\.(?P<cpuid>[^\.]+)(\.[^\.]+)$"),
            "DF": re.compile("^df\.(?P<fs>.+)(\.df_complex.+)$"),
            "DISK": re.compile("^disk\.(?P<disk>[^\.]+)(\..+)$"),
            "INTERFACE": re.compile("^interface\.(?P<interface>.+)(\.if_.+)$"),
            "LOAD": re.compile("^.*$"),
            "MEMORY": re.compile("^.*$"),
            "NODE1": re.compile("^.*$"),
            "NODE2": re.compile("^.*$"),
            "NODE3": re.compile("^.*$"),
            "NODE4": re.compile("^.*$"),
            "SET10BALANCEHS": re.compile("^.*$"),
            "SET10SESSION": re.compile("^.*$"),
            "SET11SESSION": re.compile("^.*$"),
            "SET12SESSION": re.compile("^.*$"),
            "SET13SESSION": re.compile("^.*$"),
            "SET14SESSION": re.compile("^.*$"),
            "SET15SESSION": re.compile("^.*$"),
            "SET16SESSIONHS": re.compile("^.*$"),
            "SET1ADMIN": re.compile("^.*$"),
            "SET1BALANCE": re.compile("^.*$"),
            "SET1SESSION": re.compile("^.*$"),
            "SET1SPR": re.compile("^.*$"),
            "SET2BALANCE": re.compile("^.*$"),
            "SET2SESSION": re.compile("^.*$"),
            "SET2SPR": re.compile("^.*$"),
            "SET3BALANCE": re.compile("^.*$"),
            "SET3SESSION": re.compile("^.*$"),
            "SET3SPR": re.compile("^.*$"),
            "SET4BALANCE": re.compile("^.*$"),
            "SET4SESSION": re.compile("^.*$"),
            "SET4SPR": re.compile("^.*$"),
            "SET5BALANCEHS": re.compile("^.*$"),
            "SET5SESSION": re.compile("^.*$"),
            "SET5SPR": re.compile("^.*$"),
            "SET6BALANCE": re.compile("^.*$"),
            "SET6SESSION": re.compile("^.*$"),
            "SET6SPR": re.compile("^.*$"),
            "SET7BALANCE": re.compile("^.*$"),
            "SET7SESSION": re.compile("^.*$"),
            "SET8BALANCE": re.compile("^.*$"),
            "SET8SESSIONHS": re.compile("^.*$"),
            "SET9BALANCE": re.compile("^.*$"),
            "SET9SESSION": re.compile("^.*$"),
            "SET_1_SESSION_TYPE_EDR": re.compile("^.*$"),
            "SET_1_SESSION_TYPE_GX_TGPP": re.compile("^.*$"),
            "SET_1_SESSION_TYPE_SY_V11": re.compile("^.*$"),
            "SET_SESSION_COUNT_TOTAL": re.compile("^.*$"),
            "VM": re.compile("^.*$")
        }

        self.units = {}

    @staticmethod
    def pattern_to_id(match):

        chars = ["<", ">", "[", "]"]

        sample_counter = match.string
        pattern = match.re.pattern

        if "<" not in pattern:
            # Nothing to do, counter is as is
            return sample_counter

        # Dynamic values in pattern, build the id
        try:
            dynamic_component = re.search("<.*>", pattern).group()
        except Exception as e:
            logger.error(
                "Could not turn pattern into id: {0} ".format(match.string), __file__)
            return None

        for c in chars:
            dynamic_component = dynamic_component.replace(c, "-")

        return re.sub(match.group(1), dynamic_component, match.string, count=1)

    @staticmethod
    def build_pk_key(node, source, date, vm_name, counter_match):

        pk_key = vm_name
        fixed_fields_dict = {"NODE": node, "SOURCE": source, "DATETIME": date, "VMNAME": vm_name, "INTERVAL": "300"}

        # check if there are dynamic fields
        for named_group in counter_match.re.groupindex:
            # add them all to the pk_key
            pk_key = pk_key + counter_match.group(named_group)
            fixed_fields_dict[named_group.upper()] = counter_match.group(named_group)

        return pk_key, fixed_fields_dict

    def process(self, familyObj=FamilyObject(), baseObject={}):

        files_to_process = familyObj.getFiles()

        logger.debug("Reading CISCO PCRF CSV files' contents...", __file__)

        for filePath in files_to_process:

            # Clear any previous file familyObjects
            self.units = dict()

            # Get file's name
            file_name = os.path.basename(filePath)

            familyObj.fileName = file_name

            file_match = self.filename_regex.match(file_name)

            if file_match is not None:
                node = file_match.group('node')
                source = file_match.group('source')
                date = file_match.group('date')
            else:
                logger.error("Could not obtain fixed fields from sample name {0}".format(file_name), __file__)
                continue

            try:
                # Open file for writing
                f = open(filePath, 'r')
            except IOError:
                logger.error(
                    "Could not open sample file \"{0}\" in read mode: ".format(file_name), __file__)
                continue

            for row in reader(f, delimiter=',', quotechar='"'):

                if len(row) != 4:
                    logger.error(
                        "Unexpected line length in file \"{0}\": {1}".format(file_name, row), __file__)
                    continue

                export_type = row[0]
                vm_name = row[1]
                counter = row[2]
                value = row[3]

                # apply counter regex to extract family and counter info
                unit_match = self.counter_regex.match(counter)

                if unit_match is None:
                    logger.error(
                        "Could not identify the family in the line {0} of file \"{1}\"".format(row, file_name), __file__)
                    continue

                unit_id = unit_match.group("unit_id").upper()

                try:
                    counter_match = self.units_regexes[unit_id].match(counter)
                except KeyError:
                    # Family not present in regex list
                    continue

                if counter_match is None:
                    logger.error(
                        "Could not extract the counter {0} of file \"{1}\"".format(counter, file_name),
                        __file__)
                    continue

                counter_id = self.pattern_to_id(counter_match)

                if counter_id is None:
                    logger.error(
                        "Could not find the counter id {0} of file \"{1}\"".format(counter, file_name),
                        __file__)
                    continue

                datetime = familyObj.parseEnvelopeDataTime(date)

                # Build the pk key, with no need to use the pks originating from the filename, since they are the same in this loop
                pk_key, fixed_fields = self.build_pk_key(node, source, datetime, vm_name, counter_match)

                if unit_id not in self.units.keys():
                    # new family found in sample, create the family entry with the PKs and fixed fields
                    self.units[unit_id] = {
                        pk_key: fixed_fields}

                    # Add the counter itself
                    self.units[unit_id][pk_key][counter_id.upper()] = value
                else:
                    # family has already been found. Consolidate if necessary, or create new PK entry
                    if pk_key in self.units[unit_id]:
                        self.units[unit_id][pk_key][counter_id.upper()] = value
                    else:
                        # Create the fixed fields
                        self.units[unit_id][pk_key] = fixed_fields
                        # Add the counter itself
                        self.units[unit_id][pk_key][counter_id.upper()] = value

            # Prepare documents to send to kafka
            for unit in self.units:

                familyObj.clearDocuments()
                familyObj.setUnitID(unit)

                for pk_key in self.units[unit]:

                    # Build the document
                    document = self.units[unit][pk_key]
                    try:
                        try:
                            data_time = familyObj.parseEnvelopeDataTime(document["DATETIME"])
                            granularity_sec = familyObj.parseEnvelopeGranularitySec(5)
                        except ValueError as e:
                            logger.warning("Could not build mediationEnvelope due to {0}: ".format(e), __file__)
                            continue

			# Parse DATETIME
			document["DATETIME"] = DT.strftime(DT.strptime(document["DATETIME"][:-10], "%Y-%m-%dT%H:%M:%S"), "%Y-%m-%d %H:%M:%S")

			familyObj.addDocument({"dataTime": data_time, "granularitySec": granularity_sec, "data": document})
                    except Exception, e:
                        logger.warning(
                            "Unable to process {0} in unit {1} because wrong format => {2}".format(familyObj.fileName,
                                                                                                   unit_id, e), __file__)
                        continue

                self.nextOp(familyObj=familyObj, baseObject=baseObject)
