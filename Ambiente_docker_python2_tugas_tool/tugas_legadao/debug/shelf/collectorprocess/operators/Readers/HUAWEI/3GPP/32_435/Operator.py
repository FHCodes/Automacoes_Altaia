#!/usr/bin/env python

__doc__ = \
    '''
    Huawei 3GPP 32.435 Performance XML reader

    Spec file syntax:
    <operation type="Readers" name="HUAWEI.3GPP.32_435" use_end_time="True" intervalUnit="M" />
'''

__version__ = '1.0'

__authors__ = [
                "Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>"
            ]

# Native libraries
import xml.etree.cElementTree as etree
import os
import gzip
from subprocess import call
from datetime import timedelta, datetime
import re
import io
import importlib
import copy
import cStringIO
import shlex

# Local libraries
BaseOperator = importlib.import_module("shelf.collectorprocess.operators.BaseOperator").BaseOperator
FamilyObject = importlib.import_module("shelf.collectorprocess.operators.FamilyObject").FamilyObject
logger = importlib.import_module("shelf.collectorprocess.logger").logger


def rewind(buffered_reader):
    if isinstance(buffered_reader, (io.BufferedReader, cStringIO.InputType)):
        try:
            buffered_reader.seek(0)
        except AttributeError as e:
            logger.error("Could not rewind the unzipped stream of due to {0}".format(e.message))

    return

def convertTimeZone(date):
    if '-' in date:
        d1 = datetime.strptime(date[:-6], '%Y-%m-%dT%H:%M:%S')
        d2 = datetime.strptime('0001-01-01 ' + date[-5:] + ':00', '%Y-%m-%d %H:%M:%S')
        t1 = datetime.strptime('0001-01-01 00:00:00', '%Y-%m-%d %H:%M:%S')
        return t1 + (d1 - d2)
    return datetime.strptime(date, '%Y-%m-%dT%H:%M:%S')

class Operator(BaseOperator):

    # Class Constructor
    def __init__(self, operationParams, baseObject={}):
        BaseOperator.__init__(self, operationParams, baseObject=baseObject)

        self.datetime_regex = re.compile(r'^(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}).*$')

        # Initialize end time and gp cache
        self.time_cache = dict()

        # Initialize start time calculator flag according to spec file, inverted
        self.useEndTime = False
        if "use_end_time" in self.options:
            if self.options["use_end_time"].upper() == "TRUE":
                self.useEndTime = True

        # Sets the interval unit, as default its defined to Minutes
        self.intervalUnit = 'M'
        if "intervalUnit" in self.options:
            self.intervalUnit = self.options["intervalUnit"].upper()

    def process(self, familyObj=FamilyObject(), baseObject={}):

        filesToBeProcessed = familyObj.getFiles()
        familyObj.clearFiles()

        for filePath in filesToBeProcessed:

            fileName = os.path.basename(filePath)
            originalFilePath = filePath
            familyObj.fileName = fileName
            self.timeCache = dict()

            logger.debug("Reading Huawei Performance 3GPP 32.435 XML files '{0}' contents...".format(fileName), __file__)

            #logger.warning(fileName +': '+ str(os.path.getsize(filePath)))
            if os.path.getsize(filePath) == 0:
                logger.warning("File {0} is empty.".format(fileName), __file__)
                continue
            try:
                #Open file for writing
                if os.path.splitext(originalFilePath)[1] == ".gz":
                    filePath = io.BufferedReader(gzip.open(filePath))
            except IOError:
                logger.warning("Could not open sample file \"{}\" in read mode: ".format(originalFilePath))
                continue

            try:
                self.fast_iter(filePath, familyObj, baseObject, self.getPresets(filePath))
            except Exception as ex:
                logger.error(ex)
                logger.error("Error occurred while processing file with name: {0}".format(fileName), __file__)

    def getPresets(self, filePath):
        context = iter(etree.iterparse(filePath, events=('start', 'end')))
        # get root element
        _, root = next(context)

        tag = ['fileSender', 'measCollec', 'fileFooter', 'managedElement']

        if isinstance(tag, list):
            multi = True
        else:
            multi = False

        headerDocument = dict()
        namespace = None
        for event, elem in context:
            if event == 'start' and namespace is None:
                if "}" in elem.tag:
                    namespace = elem.tag.split("}")[0].strip("{")
                    namespace = "{" + namespace + "}"
                else:
                    namespace = ""

            if multi:
                if event == 'start':
                    if elem.tag == namespace + 'fileSender':
                        headerDocument['ELEMENTTYPE'] = elem.get('elementType')
                        elem.clear()

                    elif elem.tag == namespace + 'measCollec':
                        try:
                            headerDocument['RESULT TIME'] = datetime.strftime(datetime.strptime(self.datetime_regex.match(elem.get('beginTime')).group(1), "%Y-%m-%dT%H:%M:%S"),'%Y-%m-%d %H:%M:%S')
                        except:
                            headerDocument['END TIME'] = datetime.strftime(datetime.strptime(self.datetime_regex.match(elem.get('endTime')).group(1), "%Y-%m-%dT%H:%M:%S"),'%Y-%m-%d %H:%M:%S')
                        elem.clear

                    elif elem.tag == namespace + 'managedElement':
                        headerDocument['USERLABEL'] = elem.get('userLabel')
                        elem.clear()

                elif event == 'end':
                    elem.clear()
            else:
                elem.clear()
        del context
        rewind(filePath)
        return headerDocument

    def fast_iter(self, filePath, familyObj, baseObject, headerDocument):
        context = iter(etree.iterparse(filePath, events=('start', 'end')))
        # get root element
        _, root = next(context)

        tag = ['measInfo', 'granPeriod', 'repPeriod', 'measType', 'measTypes', 'measValue', 'measResults', 'r']
        if isinstance(tag, list):
            multi = True
        else:
            multi = False

        namespace = None
        for event, elem in context:
            if event == 'start' and namespace is None:
                if "}" in elem.tag:
                    namespace = elem.tag.split("}")[0].strip("{")
                    namespace = "{" + namespace + "}"
                else:
                    namespace = ""

            if multi:
                if event == 'start':
                    if elem.tag == namespace + 'measInfo':
                        if 'measInfoId' in elem.attrib.keys():
                            self.measInfoId = elem.get('measInfoId')
                        else:
                            self.measInfoId = 'generic'
                        newDocument = copy.deepcopy(headerDocument)
                        measTypes = list()
                        measValues = list()
                        elem.clear()

                    elif elem.tag == namespace + 'granPeriod':
                        newDocument['GRANULARITY PERIOD'] = self.format_interval(int(FamilyObject.parseEnvelopeGranularitySec(elem.get('duration'))), elem.get('duration')[-1:].upper(), self.intervalUnit)
                        elem.clear()

                    elif elem.tag == namespace + 'repPeriod' and 'GRANULARITY PERIOD' not in newDocument.keys():
                        newDocument['GRANULARITY PERIOD'] = self.format_interval(int(FamilyObject.parseEnvelopeGranularitySec(elem.get('duration'))), elem.get('duration')[-1:].upper(), self.intervalUnit)
                        elem.clear()

                    elif elem.tag == namespace + 'measValue':
                        newDocument['OBJECT NAME'] = elem.get('measObjLdn')
                        elem.clear()

                elif event == 'end':
                    if elem.tag == namespace + 'measInfo':
                        pass

                    elif elem.tag == namespace + 'measType':
                        measTypes.append(elem.text.upper())
                        pass

                    elif elem.tag == namespace + 'measTypes':
                        if elem.text:
                            measTypes = (elem.text.upper()).split(' ')
                        pass

                    elif elem.tag == namespace + 'measValue':
                        #logger.error("measValues: {0}".format(measValues))
                        if len(measValues) != 0:
                            granularity_sec = newDocument['GRANULARITY PERIOD']
                            if self.useEndTime:
                                try:
                                    index = "{0}{1}".format(newDocument['GRANULARITY PERIOD'], newDocument['END TIME'])

                                    if index in self.timeCache.keys():
                                        newDocument['RESULT TIME'] = self.timeCache[index]['RT']
                                    else:
                                        self.timeCache[index] = dict()
                                        # self.timeCache[index]['gps'] = self.format_interval(int(FamilyObject.parseEnvelopeGranularitySec(newDocument['GRANULARITY PERIOD'], self.intervalUnit, 'S')))
                                        self.timeCache[index]['gps'] = self.format_interval(int(FamilyObject.parseEnvelopeGranularitySec(newDocument['GRANULARITY PERIOD'])), self.intervalUnit, 'S')

                                        # newDocument['RESULT TIME'] = (newDocument['END TIME'] - timedelta(0, self.timeCache[index]['gps']))
                                        newDocument['RESULT TIME'] = datetime.strftime((datetime.strptime(newDocument['END TIME'], '%Y-%m-%d %H:%M:%S') - timedelta(0, self.timeCache[index]['gps'])),'%Y-%m-%d %H:%M:%S')
                                        # Time cache, used to prevent unneeded beginTime calc
                                        self.timeCache[index]['RT'] = newDocument['RESULT TIME']
                                    granularity_sec = self.timeCache[index]['gps']
                                except Exception as ex:
                                    logger.error("Could not parse end time due to non matching regex with {0}: ".format(newDocument['END TIME']))
                                    logger.error("Exception: {0}".format(ex))

                            document = copy.deepcopy(newDocument)
                            document.update(dict(zip(measTypes, measValues)))
                            familyObj.setUnitID(self.measInfoId)
                            familyObj.clearDocuments()
                            data_document = {"dataTime": FamilyObject.parseEnvelopeDataTime(document['RESULT TIME']), "granularitySec": granularity_sec, "data": document}
                            familyObj.addDocument(data_document)
                            self.nextOp(familyObj=familyObj, baseObject=baseObject)

                        measValues = list()

                    elif elem.tag == namespace + 'r':
                        measValues.append(elem.text)
                        pass

                    elif elem.tag == namespace + 'measResults':
                        if elem.text:
                            measValues = shlex.split((elem.text))
                            measValues = [None if x == 'NIL' else x for x in measValues]
                    elem.clear()
            else:
                elem.clear()
        del context

    @staticmethod
    def format_interval(value, base_format, unit_format):

        matrix_data = {
            'S':
            {
                'S':
                {
                    'value': 1,
                    'operation': ''
                },
                'M':
                {
                    'value': 60,
                    'operation': '/'
                },
                'H':
                {
                    'value': 3600,
                    'operation': '/'
                }
            },
            'M':
            {
                'S':
                {
                    'value': 60,
                    'operation': '*'
                },
                'M':
                {
                    'value': 1,
                    'operation': ''
                },
                'H':
                {
                    'value': 60,
                    'operation': '/'
                }
            },
            'H':
            {
                'S':
                {
                    'value': 3600,
                    'operation': '*'
                },
                'M':
                {
                    'value': 60,
                    'operation': '*'
                },
                'H':
                {
                    'value': 1,
                    'operation': ''
                }
            }
        }

        if matrix_data[base_format][unit_format]['operation'] == '*':
            return value * matrix_data[base_format][unit_format]['value']
        elif matrix_data[base_format][unit_format]['operation'] == '/':
            return value / matrix_data[base_format][unit_format]['value']
        return value
