#!/usr/bin/env python

__doc__ = \
    '''
    Cadastros CSV construidos pela MEO
'''

__version__ = '0.1'

__authors__ = [
    "Version 1.0: Joao Pio <joao-t-pio@alticelabs.com>"
]

# import vendorConvert
import gzip
from csv import reader, Sniffer
import importlib
import os
import csv
import re
import io

# Local libraries
BaseOperator = importlib.import_module("shelf.collectorprocess.operators.BaseOperator").BaseOperator
FamilyObject = importlib.import_module("shelf.collectorprocess.operators.FamilyObject").FamilyObject
logger = importlib.import_module("shelf.collectorprocess.logger").logger


class Operator(BaseOperator):

    # Class Constructor
    def __init__(self, operationParams, baseObject={}):
        BaseOperator.__init__(self, operationParams, baseObject=baseObject)

        self.name_regex_list= [
            # Cadastro geral
            re.compile(
                "^cadastro_(?P<FAMILY>[^.]+)\.[txt|csv].*$"),
            # Cadastro SBC
            re.compile(
                "^cadastro(?P<FAMILY>[^_][^.]+)\.[txt|csv].*$"),
            # IPTV
            re.compile(
                "^iptv_(?P<FAMILY>[^.]+)\.[txt|csv].*$")
        ]

        self.date_regex_list= [
            # 20220124
            re.compile("^(?P<YEAR>19|20[0-9]{2})(?P<MONTH>1[0-2]|0[1-9])(?P<DAY>3[0-1]|0[1-9]|[1-2][0-9])$"),
            # 2022-02-13 07:31:00
            re.compile(
                "^(?P<YEAR>19|20[0-9]{2})-(?P<MONTH>1[0-2]|0[1-9])-(?P<DAY>3[0-1]|0[1-9]|[1-2][0-9])[T ](?P<HOUR>2[0-3]|[0-1][0-9]):(?P<MIN>[0-5][0-9]):(?P<SEC>[0-5][0-9])$")
        ]

    def file_delimiter_detector(self, file):

        sniffer = Sniffer()
        sniffer.preferred = [';', ',']
        dialect = sniffer.sniff(file.readline())
        file.seek(0)
        return dialect.delimiter

    def process(self, familyObj=FamilyObject(), baseObject={}):

        for file_path in familyObj.files:

            # Get file's name
            familyObj.fileName = os.path.basename(file_path)

            if os.path.getsize(file_path) == 0:
                logger.warning("File {0} is empty.".format(file_path), __file__)
                continue

            try:
                # If file is compressed, open with a buffered stream
                if os.path.splitext(file_path)[1] == ".gz":
                    f = io.BufferedReader(gzip.open(file_path))

                    # Sligthly less efficient alternative for large files, but slightly faster for smaller files.
                    # Keep this in comment, if case circumstances change
                    # p = subprocess.Popen(["zcat", file_path], stdout=subprocess.PIPE)
                    # file_path = cStringIO.StringIO(p.communicate()[0])
                else:
                    # Open file for writing
                    f = open(file_path, 'r')

            except IOError:
                logger.error("Could not open sample file \"{0}\" in read mode: ".format(familyObj.fileName), __file__)
                continue

            # Detect the CSV file delimiter character (preferred ones are ','  and ';')
            try:
                delimiter = self.file_delimiter_detector(f)
            except csv.Error:
                logger.error("Could not identify csv delimiter in file  \"{0}\"".format(familyObj.fileName), __file__)
                continue

            # Iterates all the regexes and tries to match them with the data_time provided.
            groups = next((reg.match(familyObj.fileName) for reg in self.name_regex_list if reg.match(familyObj.fileName)),
                          False)

            if not groups:
                logger.error("Could not identify family id from file name \"{0}\": ".format(familyObj.fileName), __file__)
                continue
            else:
                # Extract family id
                familyObj.unitID = groups.group("FAMILY").upper()

            column_names = None

            try:
                for n, line in enumerate(reader(f, delimiter=delimiter)):

                    line = [item.decode("latin-1") for item in line]

                    # CSV Header
                    if n == 0:

                        # Fix name of first element of row that has a # character attached
                        if len(line) > 0:
                            line[0] = line[0].strip("#")

                            # Store column names into a list
                            column_names = [name.upper() for name in line]

                            # Detect what is the date field of this particular sample
                            for date_field in ["DATA", "DIA"]:
                                if date_field in column_names: break
                        else:
                            logger.error("Could not retrieve column names from first row of sample '{0}'".format(
                                familyObj.fileName), __file__)
                            break

                    else:
                        if len(line) == len(column_names):

                            document = dict(zip(column_names, line))

                            try:
                                # Iterates all the regexes and tries to match them with the data_time provided.
                                groups = next((reg.match(document[date_field]) for reg in self.date_regex_list if
                                               reg.match(document[date_field])),
                                              False)

                                if not groups:
                                    logger.error(
                                        "Could not process date_field with content \"{0}\" from file {1}: ".format(document[date_field], familyObj.fileName),
                                        __file__)
                                    continue
                                else:
                                    document[date_field] = "{0}-{1}-{2} 00:00:00".format(groups.group("YEAR"), groups.group("MONTH"), groups.group("DAY"))
                            except KeyError:
                                logger.error(
                                    "No proper date_field exists in file \"{0}\": ".format(familyObj.fileName),
                                    __file__)
                                break

                            try:
                                data_time = familyObj.parseEnvelopeDataTime(document[date_field])
                            except ValueError as e:
                                logger.warning("Could not build mediationEnvelope due to {0}: ".format(e), __file__)
                                continue
                            document["STARTTIME"] = document[date_field]

                            # envelope
                            familyObj.addDocument({"dataTime": data_time, "granularitySec": 1440, "data": document})
                            self.nextOp(familyObj=familyObj, baseObject=baseObject)
                            familyObj.clearDocuments()
                        else:
                            logger.warning(
                                "Number of values in line {0} is different than number of announced columns in sample '{1}'".format(
                                    n, familyObj.fileName))

            except csv.Error, e:
                logger.warning("{0} in line {1} of file {2}".format(e, n, familyObj.fileName))
