#!/usr/bin/env python

__doc__ = '''
    This object is the vehicle for passing data between operations 
'''

__version__ = '0.1'

__authors__ = [
    "Version 0.1: Francisco Santiago <francisco-j-santiago@telecom.pt>"
    "Version 2.0: Joao Pio <joao-t-pio@telecom.pt>"
]

from .SplittableObject import SplittableObject
import re


class FamilyObject(SplittableObject):

    _dateDefaultDict = {
        "YEAR": "1970",
        "MONTH": "01",
        "DAY": "01",
        "HOUR": "00",
        "MIN": "00",
        "SEC": "00",
        "MSEC": "000",
        "TIMEZONE": "+00:00",
        "HFORMAT": ""
    }

    _dateTranslationDict = {
        "YEAR": {},
        "MONTH": {"Jan": "01", "Feb": "02", "Mar": "03", "Apr": "04", "May": "05", "Jun": "06", "Jul": "07",
                  "Aug": "08", "Sep": "09", "Oct": "10", "Nov": "11", "Dec": "12"},
        "DAY": {},
        "HOUR": {},
        "MIN": {},
        "SEC": {},
        "MSEC": {},
        "TIMEZONE": {}
    }

    _dateKnownRegexes = [
        # Huawei XML - 2018-06-29T02:00:00.000-03:00
        re.compile(
            "^(?P<YEAR>19|20[0-9]{2})-(?P<MONTH>1[0-2]|0[1-9])-(?P<DAY>3[0-1]|0[1-9]|[1-2][0-9])T(?P<HOUR>2[0-3]|[0-1][0-9]):(?P<MIN>[0-5][0-9]):(?P<SEC>[0-5][0-9])\.(?P<MSEC>[0-9]+)?(?P<TZHOUR>[+-][0-2][0-9]):(?P<TZMIN>[0-5][0-9])$"),
        # Huawei CSV	- 2018-07-07 12:00
        re.compile(
            "^(?P<YEAR>19|20[0-9]{2})-(?P<MONTH>1[0-2]|0[1-9])-(?P<DAY>3[0-1]|0[1-9]|[1-2][0-9])\s(?P<HOUR>2[0-3]|[0-1][0-9]):(?P<MIN>[0-5][0-9])$"),
        # NSN XML - 2018-06-29T02:00:00.000-03:00:00
        re.compile(
            "^(?P<YEAR>19|20[0-9]{2})-(?P<MONTH>1[0-2]|0[1-9])-(?P<DAY>3[0-1]|0[1-9]|[1-2][0-9])T(?P<HOUR>2[0-3]|[0-1][0-9]):(?P<MIN>[0-5][0-9]):(?P<SEC>[0-5][0-9])\.(?P<MSEC>[0-9]+)?(?P<TZHOUR>[+-][0-2][0-9]):(?P<TZMIN>[0-5][0-9]):(?P<TZSEC>[0-5][0-9])$"),
        # ERICSSON ASN1 - 20180707120000-0300
        re.compile(
            "^(?P<YEAR>19|20[0-9]{2})(?P<MONTH>1[0-2]|0[1-9])(?P<DAY>3[0-1]|0[1-9]|[1-2][0-9])(?P<HOUR>2[0-3]|[0-1][0-9])(?P<MIN>[0-5][0-9])(?P<SEC>[0-5][0-9])(?P<TZHOUR>[+-][0-2][0-9])(?P<TZMIN>[0-5][0-9])$"),
        # ERICSSON XML/NOKIA NSP PM 2018-06-29 02:00:00
        re.compile(
            "^(?P<YEAR>19|20[0-9]{2})-(?P<MONTH>1[0-2]|0[1-9])-(?P<DAY>3[0-1]|0[1-9]|[1-2][0-9])[T ](?P<HOUR>2[0-3]|[0-1][0-9]):(?P<MIN>[0-5][0-9]):(?P<SEC>[0-5][0-9])$"),
        # PTIN IMS LRF / MAHINDRA COMVIVA CM 20180707120000
        re.compile(
            "^(?P<YEAR>19|20[0-9]{2})(?P<MONTH>1[0-2]|0[1-9])(?P<DAY>3[0-1]|0[1-9]|[1-2][0-9])(?P<HOUR>2[0-3]|[0-1][0-9])(?P<MIN>[0-5][0-9])(?P<SEC>[0-5][0-9])$"),
        # PTIN IMS SEC 1803182345
        re.compile(
            "^(?P<YEAR>[0-9]{2})(?P<MONTH>1[0-2]|0[1-9])(?P<DAY>3[0-1]|0[1-9]|[1-2][0-9])(?P<HOUR>2[0-3]|[0-1][0-9])(?P<MIN>[0-5][0-9])$"),
        # NOKIA NSP PM Nov 15, 2018 11:10:38 PM
        re.compile(
            "^(?P<MONTH>Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) (?P<DAY>3[0-1]|0[1-9]|[1-9]|[1-2][0-9]), (?P<YEAR>19|20[0-9]{2}) (?P<HOUR>1[0-2]|[1-9]):(?P<MIN>[0-5][0-9]|[0-9]):(?P<SEC>[0-5][0-9]|[0-9]) (?P<HFORMAT>AM|PM)$"),
        # NOKIA NSP CM 20181115
        re.compile("^(?P<YEAR>19|20[0-9]{2})(?P<MONTH>1[0-2]|0[1-9])(?P<DAY>3[0-1]|0[1-9]|[1-2][0-9])$"),
        # NOKIA NETACT CORE FLEXING 2019-02-07T23:30:00-02:00
        re.compile(
            "^(?P<YEAR>19|20[0-9]{2})-(?P<MONTH>1[0-2]|0[1-9])-(?P<DAY>3[0-1]|0[1-9]|[1-2][0-9])T(?P<HOUR>2[0-3]|[0-1][0-9]):(?P<MIN>[0-5][0-9]):(?P<SEC>[0-5][0-9])(?P<TZHOUR>[+-][0-2][0-9]):(?P<TZMIN>[0-5][0-9])$"),
        # HP LBS NBI Thu May 06 00:00:00 COT 2017 / 201705110000
        re.compile(
            "^(?P<WEEKDAY>Mon|Tue|Wed|Thu|Fri|Sat|Sun) (?P<MONTH>Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) (?P<DAY>3[0-1]|0[1-9]|[1-2][0-9]) (?P<HOUR>[0-2][0-9]):(?P<MIN>[0-5][0-9]):(?P<SEC>[0-5][0-9]) \w+ (?P<YEAR>19|20[0-9]{2})$"),
        re.compile(
            "^(?P<YEAR>19|20[0-9]{2})(?P<MONTH>1[0-2]|0[1-9])(?P<DAY>3[0-1]|0[1-9]|[1-2][0-9])(?P<HOUR>2[0-3]|[0-1][0-9])(?P<MIN>[0-5][0-9])$"),
        # NOVITECH VOICEMAIL 20181123 00:00
        re.compile(
            "^(?P<YEAR>19|20[0-9]{2})(?P<MONTH>1[0-2]|0[1-9])(?P<DAY>3[0-1]|0[1-9]|[1-2][0-9]) (?P<HOUR>2[0-3]|[0-1][0-9]):(?P<MIN>[0-5][0-9])$"),
        # TELCORDIA ISCP IN 2018/11/23 00:00
        re.compile(
            "^(?P<YEAR>19|20[0-9]{2})\/(?P<MONTH>1[0-2]|0[1-9])\/(?P<DAY>3[0-1]|0[1-9]|[1-2][0-9]) (?P<HOUR>2[0-3]|[0-1][0-9]):(?P<MIN>[0-5][0-9])$"),
        # TELCORDIA CUSTOM CPLISTREPORT CONTROLSEGMENTUSAGE 20181123
        re.compile(
            "^(?P<YEAR>19|20[0-9]{2})(?P<MONTH>1[0-2]|0[1-9])(?P<DAY>3[0-1]|0[1-9]|[1-2][0-9])$"),
        # HUAWEI U2000 PM, 2019-01-03 21:00:00
        re.compile(
            "^(?P<YEAR>19|20[0-9]{2})-(?P<MONTH>1[0-2]|0[1-9])-(?P<DAY>3[0-1]|0[1-9]|[1-2][0-9])\s(?P<HOUR>2[0-3]|[0-1][0-9]):(?P<MIN>[0-5][0-9]):(?P<SEC>[0-5][0-9])$"),
        # MAHINDRA COMVIVA PM 11-01-2019 01:43:58.000000
        re.compile(
            "^(?P<DAY>3[0-1]|0[1-9]|[1-2][0-9])-(?P<MONTH>1[0-2]|0[1-9])-(?P<YEAR>19|20[0-9]{2})\s(?P<HOUR>2[0-3]|[0-1][0-9]):(?P<MIN>[0-5][0-9]):(?P<SEC>[0-5][0-9])\.(?P<MSEC>[0-9]+)?$"),
        # MAHINDRA COMVIVA PM 20190111_013000
        re.compile(
            "^(?P<YEAR>19|20[0-9]{2})(?P<MONTH>1[0-2]|0[1-9])(?P<DAY>3[0-1]|0[1-9]|[1-2][0-9])_(?P<HOUR>2[0-3]|[0-1][0-9])(?P<MIN>[0-5][0-9])(?P<SEC>[0-5][0-9])$"),
        # ERICSSON 32.401 DTD 20190111013000Z
        re.compile(
            "^(?P<YEAR>19|20[0-9]{2})(?P<MONTH>1[0-2]|0[1-9])(?P<DAY>3[0-1]|0[1-9]|[1-2][0-9])(?P<HOUR>2[0-3]|[0-1][0-9])(?P<MIN>[0-5][0-9])(?P<SEC>[0-5][0-9])[Z]*$"),
        #ONMOBILE
        re.compile("^(?P<YEAR>[0-9]{4})-(?P<MONTH>1[0-2]|0[1-9])-(?P<DAY>3[0-1]|0[0-9]|[1-2][0-9]) (?P<HOUR>2[0-3]|[0-1][0-9]|[0-9]):(?P<MIN>[0-5][0-9]):(?P<SEC>[0-5][0-9])$"),
        #MAHINDRA
        re.compile("^(?P<DAY>3[0-1]|0[0-9]|[1-2][0-9])-(?P<MONTH>1[0-2]|0[1-9])-(?P<YEAR>[0-9]{4}) (?P<HOUR>2[0-3]|[0-1][0-9]|[0-9]):(?P<MIN>[0-5][0-9]):(?P<SEC>[0-5][0-9])*$"),
        # NSN XML MMTL - 2020-11-12T10:30:01Z
        re.compile("^(?P<YEAR>2[0-9]{3})-(?P<MONTH>1[0-2]|0[1-9])-(?P<DAY>3[0-1]|0[1-9]|[1-2][0-9])T(?P<HOUR>2[0-3]|[0-1][0-9]):(?P<MIN>[0-5][0-9]):(?P<SEC>[0-5][0-9])[zZ]$"),
        # ALB AGORA 3GPP XML 2021-11-23T23:45:00.000Z
        re.compile(
            "^(?P<YEAR>2[0-9]{3})-(?P<MONTH>1[0-2]|0[1-9])-(?P<DAY>3[0-1]|0[1-9]|[1-2][0-9])T(?P<HOUR>2[0-3]|[0-1][0-9]):(?P<MIN>[0-5][0-9]):(?P<SEC>[0-5][0-9])\.000[zZ]$")
    ]

    _granularityDefaultDict = {
        "SECS": "00"
    }

    _granularityKnownRegexes = [
        # Huawei XML
        re.compile("^PT(?P<SECS>\d+)S$"),
        re.compile("^PT(?P<SECS>\d+)\D$"),
        # Huawei CSV/NSN XML/ERICSSON ASN1/ERICSSON XML/PTIN_IMS/NOKIA NSP CM & PM/HP LBS NBI
        re.compile("^(?P<SECS>\d+)$")
    ]


    # Class Constructor
    def __init__(self, baseObject={}):

        self._unitID = None
        self._documents = list()
        self._sources = list()
        self._files = list()
        self._fileName = ""
        self._nDocs = 0
        self._nSources = 0

    def getUnitID(self):
        return self._unitID

    def setUnitID(self, unitID):
        self._unitID = unitID.upper()

    def getDocuments(self):
        return self._documents

    def setDocuments(self, documents):
        self._documents = documents

    def addDocument(self, document):
        self.nDocs += 1
        self.documents.append(document)

    def addSource(self, source):
        self.nSources += 1
        self.sources.append(source)

    def getFiles(self):
        return self._files

    def setFiles(self, files):
        self._files = files

    def clearDocuments(self):
        self.nDocs = 0
        self.documents = list()

    def clearSources(self):
        self.nSources = 0
        self.sources = list()

    def clearFiles(self):
        self._files = list()

    @property
    def unitID(self):
        return self._unitID

    @unitID.setter
    def unitID(self, value):
        self._unitID = value

    @property
    def documents(self):
        return self._documents

    @documents.setter
    def documents(self, value):
        self._documents = value

    @property
    def files(self):
        return self._files

    @files.setter
    def files(self, value):
        self._files = value

    @property
    def fileName(self):
        return self._fileName

    @fileName.setter
    def fileName(self, value):
        self._fileName = value

    @property
    def nDocs(self):
        return self._nDocs

    @nDocs.setter
    def nDocs(self, value):
        self._nDocs = value

    @property
    def nSources(self):
        return self._nSources

    @nSources.setter
    def nSources(self, value):
        self._nSources = value

    @property
    def sources(self):
        return self._sources

    @sources.setter
    def sources(self, value):
        self._sources = value

    # Parses the dataTime field for a document, necessary for the mediation envelope to be sent by Kafka Event
    @classmethod
    def parseEnvelopeDataTime(cls, data_time, regex=None):

        # Copy default date dictionary for processing
        date_dict = cls._dateDefaultDict.copy()

        # If regex is not provided by reader
        if regex is None:
            # Iterates all the regexes and tries to match them with the data_time provided.
            groups = next((reg.match(data_time) for reg in cls._dateKnownRegexes if reg.match(data_time)), False)
        # Regex is provided by reader
        else:
            groups = regex.match(data_time)

        if groups:
            groups = groups.groupdict()

            for key in date_dict.keys():

                if key in groups.keys():
                    if groups[key] is not None:
                        date_dict[key] = groups[key]

                if key == "TIMEZONE":
                    if "TZHOUR" in groups.keys() and "TZMIN" in groups.keys():
                        date_dict[key] = "{0}:{1}".format(groups["TZHOUR"], groups["TZMIN"])

            # add customizations here

            # IMS SEC year needs to be YYYY format
            if len(date_dict) == 2:
                date_dict["YEAR"] = "20{0}".format(date_dict["YEAR"])

            # NOKIA NSP CM month needs to be converted to a number
            try:
                month = int(date_dict["MONTH"])
            except ValueError:
                try:
                    date_dict["MONTH"] = cls._dateTranslationDict["MONTH"][date_dict["MONTH"]]
                except KeyError:
                    raise ValueError("parseEnvelopeDataTime: Unrecognizable data_time pattern: {0}".format(data_time))

            # NOKIA NSP Hour format (AM or PM) needs to be taken into the calculations
            if date_dict["HFORMAT"] == "AM":
                date_dict["HOUR"] = int(date_dict["HOUR"]) % 12
            elif date_dict["HFORMAT"] == "PM":
                date_dict["HOUR"] = 12 + (int(date_dict["HOUR"]) % 12)
        else:
            raise ValueError("parseEnvelopeDataTime: Unrecognizable data_time pattern: {0}".format(data_time))

        return "{0:04d}-{1:02d}-{2:02d}T{3:02d}:{4:02d}:{5:02d}.{6:03d}{7}".format(int(date_dict["YEAR"]),
                                                                                   int(date_dict["MONTH"]),
                                                                                   int(date_dict["DAY"]),
                                                                                   int(date_dict["HOUR"]),
                                                                                   int(date_dict["MIN"]),
                                                                                   int(date_dict["SEC"]),
                                                                                   int(date_dict["MSEC"]),
                                                                                   date_dict["TIMEZONE"])

    # Parses the dataTime field for a document, necessary for the mediation envelope to be sent by Kafka Event
    @classmethod
    def parseEnvelopeGranularitySec(cls, granularitySec):

        # Copy default granularity dictionary for processing
        granularity_dict = cls._granularityDefaultDict.copy()

        # Guarantee we have a string instead of an int
        granularitySec = str(granularitySec)

        groups = next((reg.match(granularitySec) for reg in cls._granularityKnownRegexes if reg.match(granularitySec)),
                      False)

        if groups:
            groups = groups.groupdict()

            for key in granularity_dict.keys():
                if key in groups.keys():
                    if groups[key] is not None:
                        granularity_dict[key] = groups[key]
        else:
            raise ValueError(
                "parseEnvelopeGranularitySec: Unrecognizable granularitySec pattern: {0}".format(granularitySec))

        return "{0}".format(granularity_dict["SECS"])

    def splitObject(self, nObjects):

        objects = list()

        len_files = len(self.files)
        len_sources = len(self.sources)

        if len_files < nObjects and len_sources < nObjects:
            objects.append(self)
        else:

            if len_files % nObjects == 0:
                n_files_for_each = len_files / nObjects
            else:
                n_files_for_each = len_files / nObjects + 1

            if len_sources % nObjects == 0:
                n_sources_for_each = len_sources / nObjects
            else:
                n_sources_for_each = len_sources / nObjects + 1

            split_file_list = list()
            len_split_file_list = 0
            if n_files_for_each:
                split_file_list = [x for x in self.divideInSublists(self.files, nObjects)]
                len_split_file_list = len(split_file_list)

            split_source_list = list()
            len_split_source_list = 0
            if n_sources_for_each:
                split_source_list = [x for x in self.divideInSublists(self.sources, nObjects)]
                len_split_source_list = len(split_source_list)

            n_documents_for_each = len(self.documents) / nObjects
            split_document_list = list()
            len_split_document_list = 0
            if n_documents_for_each:
                split_document_list = [x for x in self.divideInSublists(self.documents, nObjects)]
                len_split_document_list = len(split_document_list)

            for i in range(nObjects):
                newFamilyObject = FamilyObject()

                if len_split_file_list > i:
                    newFamilyObject.files = split_file_list[i]
                else:
                    newFamilyObject.files = list()

                if len_split_source_list > i:
                    newFamilyObject.sources = split_source_list[i]
                else:
                    newFamilyObject.sources = list()

                if len_split_document_list > i:
                    newFamilyObject.documents = split_document_list[i]
                else:
                    newFamilyObject.documents = list()

                newFamilyObject.unitID = self.unitID
                newFamilyObject.fileName = self.fileName

                objects.append(newFamilyObject)

        return objects
