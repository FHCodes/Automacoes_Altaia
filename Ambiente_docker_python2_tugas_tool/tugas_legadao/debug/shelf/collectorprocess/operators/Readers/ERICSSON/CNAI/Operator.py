#!/usr/bin/env python

__doc__ = \
    '''
    ERICSSON CNAI EXPORT Parameters reader

    Spec file syntax:
    <operation type="Readers" name="ERICSSON.CNAI" prepoc_path="/opt/alticelabs/namf/tools/shelf" />
'''

__version__ = '1.0'

__authors__ = [
    "Version 1.0: Joao Pio <joao-t-pio@alticelabs.com>"
]

# Native libraries
import re
import os
import importlib
from csv import reader
import csv
import subprocess

# Local libraries
BaseOperator = importlib.import_module("shelf.collectorprocess.operators.BaseOperator").BaseOperator
FamilyObject = importlib.import_module("shelf.collectorprocess.operators.FamilyObject").FamilyObject
logger = importlib.import_module("shelf.collectorprocess.logger").logger


class Operator(BaseOperator):
    # Class Constructor
    def __init__(self, operationParams, baseObject={}):
        BaseOperator.__init__(self, operationParams, baseObject=baseObject)

        self.filename_regex = re.compile("^CNAI_EXPORT.*$")
        self.family_filename_regex = re.compile("^(.*)\.csv$")
        self.bsc_filename_regex = re.compile("^.*BSC\.csv$")

        self.BSC = dict()

        self.preparser_default_location = '/opt/alticelabs/namf/tools/ericssoncnaiparser.jar'

    def process(self, familyObj=FamilyObject(), baseObject={}):

        logger.debug("Reading ERICSSON CNAI export CSV file' contents...", __file__)

        try:
            # Assume preparser path given by spec file
            preparser_location = self.options["preproc_path"]
        except KeyError:
            # choose default preprocessor path
            preparser_location = self.preparser_default_location

        file_path = familyObj.getFiles()[0]

        familyObj.clearDocuments()

        # Raw file name, before being preprocessed
        file_name = os.path.basename(file_path)

        # check if the output sub folder for preprocessed files exists
        output_folder = os.path.join(os.path.dirname(file_path), "preprocessed_{0}".format(file_name))

        if not os.path.exists(output_folder):

            # define the access rights
            access_rights = 0o777

            try:
                os.mkdir(output_folder, access_rights)
            except OSError:
                error_message = "Could not create subdirectory for preprocessed files {0}".format(output_folder)
                logger.error(error_message, __file__)
                raise Exception(error_message)

        if os.path.exists(preparser_location):
            result = subprocess.check_call(['java', '-jar', preparser_location, '-i', file_path, '-o', output_folder])
        else:
            error_message = "Could not locate CNAI preparser in the expected location '{0}'".format(preparser_location)
            logger.error(error_message, __file__)
            raise Exception(error_message)

        # Obtain the output files list
        for root, dirs, files in os.walk(output_folder):
            filt = filter(self.family_filename_regex.match, files)

            # Keep MSC file name
            bsc_filt = filter(self.bsc_filename_regex.match, files)
            bsc_file_path = [os.path.join(root, x) for x in bsc_filt]

            preprocessed_files = [os.path.join(root, x) for x in filt]
            break

        # Build bsc dictionary
        if len(bsc_file_path) != 0:
            try:
                # Open file for writing
                bsc_file = open(bsc_file_path[0], 'r')
            except IOError:
                error_message = "Could not open BSC family file"
                logger.error(error_message, __file__)
                raise Exception(error_message)

            columns_names = list()

            for line in reader(bsc_file, delimiter=',', quotechar='"'):
                if not line:
                    continue

                line = [item.replace('"', "") for item in line]

                # find header
                if len(columns_names) == 0:
                    # capitalize the header
                    columns_names = [x.upper() for x in line]
                    continue

                # unexpected line length
                if len(line) != len(columns_names):
                    continue

                line_dict = dict(zip(columns_names, line))

                try:
                    self.BSC[line_dict["BSC_NAME"].upper()] = line_dict["MSC_NAME"].upper()
                except KeyError:
                    # unusable line
                    continue
        else:
            error_message = "Could not locate BSC family in the preprocessing result files"
            logger.error(error_message)
            raise Exception(error_message)

        for file in preprocessed_files:

            familyObj.clearDocuments()
            familyObj.fileName = os.path.basename(file)

            # get family id from filename
            try:
                unit_id = self.family_filename_regex.match(os.path.basename(file)).group(1)
                familyObj.setUnitID(unit_id)
            except AttributeError:
                logger.error(
                    "Could not obtain unit id from sample filename \"{0}\".".format(file_name), __file__)
                continue

            try:
                # Open file for writing
                f = open(file, 'r')
            except IOError:
                logger.error(
                    "Could not open sample file \"{0}\" in read mode.".format(file_name), __file__)
                continue

            columns_names = list()

            for line in reader(f, delimiter=',', quotechar='"'):
                if not line:
                    continue

                line = [item.replace('"', "") for item in line]

                # find header
                if len(columns_names) == 0:
                    # capitalize the header
                    columns_names = [x.upper() for x in line]
                    continue

                # unexpected line length
                if len(line) != len(columns_names):
                    continue

                try:
                    document = dict(zip(columns_names, line))

                    # add granularity period
                    document["GRANULARITYPERIOD"] = 1440

                    # Add MSC_NAME if it is needed
                    if "MSC_NAME" not in document.keys():
                        try:
                            msc_name = self.BSC[document["BSC_NAME"].upper()]
                            document["MSC_NAME"] = msc_name.upper()
                        except KeyError:
                            # Could not enrich
                            pass

                    try:
                        data_time = familyObj.parseEnvelopeDataTime(document["DATETIME"])
                    except ValueError as e:
                        logger.warning("Could not build mediationEnvelope due to {0}: ".format(e), __file__)
                        continue

                    # envelope
                    familyObj.addDocument({"dataTime": data_time, "granularitySec": 1440, "data": document})
                    self.nextOp(familyObj=familyObj, baseObject=baseObject)
                    familyObj.clearDocuments()

                except Exception as e:
                    logger.error("Unable to process {0} in unit {1} because wrong format => {2}".format(file_name, familyObj.getUnitID, e), __file__)
                    continue
