__version__ = '1.0'

__doc__ = '''
    Mahindra TSLEE Plat Performance IN CSV Reader
'''

__authors__ = [
    "Version 1.0: <joao-t-pio@alticelabs.com>"
]

import os
import re
from csv import reader
import importlib
import math
from datetime import datetime, timedelta

# Local libraries
BaseOperator = importlib.import_module("shelf.collectorprocess.operators.BaseOperator").BaseOperator
FamilyObject = importlib.import_module("shelf.collectorprocess.operators.FamilyObject").FamilyObject
logger = importlib.import_module("shelf.collectorprocess.logger").logger


class Operator(BaseOperator):

    # Class constructor
    def __init__(self, operationParams, baseObject={}):
        BaseOperator.__init__(self, operationParams, baseObject=baseObject)

        self.file_name_regex = re.compile(r'^(?P<ne_name>[^_]+?)_(?P<unit_id>.+?)_Last(?P<g_period>\d+?)min_(?P<date>[^\.]+?)\.csv$')
        self.date_regex = re.compile(r'^(?P<YEAR>19|20[0-9]{2})(?P<MONTH>1[0-2]|0[1-9])(?P<DAY>3[0-1]|0[1-9]|[1-2][0-9])(?P<HOUR>2[0-3]|[0-1][0-9])(?P<MIN>[0-5][0-9])(?P<SEC>[0-5][0-9])$')

    def process(self, familyObj=FamilyObject(), baseObject={}):
        logger.debug("Mahindra TSLEE Plat Performance IN file contents...", __file__)
        files_to_proceess = familyObj.getFiles()
        familyObj.clearDocuments()

        for file_path in files_to_proceess:
            familyObj.clearDocuments()

            file_name = os.path.basename(file_path)
            familyObj.fileName = file_name

            # If file is empty, bota fora :)
            if os.path.getsize(file_path) == 0:
                logger.warning("File {0} is empty.".format(file_name), __file__)
                continue

            # Try opening the file
            try:
                f = open(file_path, "r")
            except IOError:
                logger.error("Could not open file \"{0}\" in read mode.".format(file_name), __file__)

            # Get Unit ID from file name
            file_match = self.file_name_regex.match(file_name)
            if file_match is None:
                logger.error("Could not match file name  \"{0}\".".format(file_name), __file__)
                continue

            unit_id = file_match.group('unit_id').upper()
            familyObj.setUnitID(unit_id)

            # Get granularity period from file name
            g_period = file_match.group('g_period')
            gperiod_delta = timedelta(minutes=int(g_period))

            # Date handling
            try:
                date = datetime.strptime(file_match.group('date'), "%Y%m%d%H%M%S")
            except ValueError:
                logger.error("Could not match file name date \"{0}\".".format(file_match.group('date')), __file__)
                continue

            # Sort CSV file in order to group counters
            sorted_csv = sorted(reader(f, delimiter=';'))

            try:
                header = ["TYPE", "VERSION", "COUNTER", "VALUE", "RATE"]

                types_dict = dict()
                common_fields = dict()

                # Add GRANULARITYPERIOD
                common_fields["GRANULARITYPERIOD"] = g_period
                # Add NE NAME
                common_fields["NE_NAME"] = file_match.group('ne_name')

                # Add and treat ENDTIME
                if date.minute not in [0, 15, 30, 45]:
                    end_minutes = (math.floor(date.minute / 15)) * 15

                    # Flip hour
                    if end_minutes == 60:
                        date = date.replace(hour=date.hour + 1, minute=0)
                    else:
                        date = date.replace(minute=int(end_minutes))

                common_fields["ENDTIME"] = date.strftime("%Y-%m-%d %H:%M:%S")

                # Calculate STARTTIME
                common_fields["STARTTIME"] = (date - gperiod_delta).strftime("%Y-%m-%d %H:%M:%S")

                for line in sorted_csv:

                    # get type and create a document if it's the first time this type appears in the sample
                    if line[0].upper() not in types_dict:
                        types_dict[line[0].upper()] = list()

                    document_list = types_dict[line[0].upper()]
                    sample_line = dict()

                    # Gather all columns into their specific fields
                    for cnt, column in enumerate(header):
                        sample_line[column] = line[cnt]

                    # Remove spaces from counter name
                    sample_line["COUNTER"] = sample_line["COUNTER"].replace(' ', '').upper()
                    # Remove unwanted counter
                    sample_line.pop("RATE")

                    document_list.append(sample_line)

            except Exception as e:
                logger.warning("{2} - Unable to process {0} due to {1}: ".format(familyObj.fileName, e, type(e)),
                           __file__)

            for type in types_dict:

                # initialize document with common fields
                document = dict(common_fields)

                document["TYPE"] = type

                for sample_line in types_dict[type]:
                    document[sample_line["COUNTER"]] = sample_line["VALUE"]
                    document["VERSION"] = sample_line["VERSION"]


                # Parse envelope DataTime
                try:
                    timestamp = familyObj.parseEnvelopeDataTime(common_fields["STARTTIME"])
                except ValueError as e:
                    logger.warning("Could not build mediationEnvelope due to {0}: ".format(e), __file__)
                    continue

                familyObj.addDocument({"dataTime": timestamp, "granularitySec": int(g_period) * 60, "data": document})
                self.nextOp(familyObj=familyObj, baseObject=baseObject)
                familyObj.clearDocuments()
