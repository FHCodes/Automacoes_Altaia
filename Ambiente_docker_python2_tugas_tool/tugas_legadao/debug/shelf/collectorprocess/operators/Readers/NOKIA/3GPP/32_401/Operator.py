#!/usr/bin/env python

__doc__ = \
    '''
    Nokia 3GPP 32.401 Performance XML reader

    Spec file syntax:
    <operation type="Readers" name="NOKIA.3GPP.32_401" use_end_time="True" process_me="False" minfo_optionals="False" />
'''

__version__ = '1.0'

__authors__ = [
                "Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>"
            ]

# Native libraries
import xml.etree.cElementTree as etree
import os
import gzip
import cStringIO
from datetime import timedelta, datetime
import io
import re
import importlib
import copy

# Local libraries
BaseOperator = importlib.import_module("shelf.collectorprocess.operators.BaseOperator").BaseOperator
FamilyObject = importlib.import_module("shelf.collectorprocess.operators.FamilyObject").FamilyObject
logger = importlib.import_module("shelf.collectorprocess.logger").logger

def convertTimeZone(date):
    if '-' in date:
        d1 = datetime.strptime(date[:-6], '%Y-%m-%dT%H:%M:%S')
        return d1
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
                self.useEndTime = False

    def process(self, familyObj=FamilyObject(), baseObject={}):

        filesToBeProcessed = familyObj.getFiles()
        familyObj.clearFiles()

        for filePath in filesToBeProcessed:

            fileName = os.path.basename(filePath)
            familyObj.fileName = fileName
            self.timeCache = dict()

            logger.debug("[Reader] Reading Nokia Performance 3GPP 32.401 XML files '{0}' contents...".format(fileName), __file__)

            #logger.warning(fileName +': '+ str(os.path.getsize(filePath)))
            if os.path.getsize(filePath) == 0:
                logger.warning("File {0} is empty.".format(fileName), __file__)
                continue

            self.fast_iter(filePath, familyObj, baseObject, self.getPresets(filePath))

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
                        headerDocument['LOCALDN'] = elem.get('localDn')
                        headerDocument['ELEMENTTYPE'] = elem.get('elementType')
                        elem.clear()

                    elif elem.tag == namespace + 'measCollec':
                        if 'beginTime' in elem.attrib.keys() and self.useEndTime:
                            headerDocument['BEGINTIME'] = datetime.strptime(self.datetime_regex.match(elem.get('beginTime')).group(1), "%Y-%m-%dT%H:%M:%S")
                        elif 'endTime' in elem.attrib.keys():
                            headerDocument['ENDTIME'] = datetime.strptime(self.datetime_regex.match(elem.get('endTime')).group(1), "%Y-%m-%dT%H:%M:%S")
                        elem.clear()

                    elif elem.tag == namespace + 'managedElement':
                        headerDocument['SWVERSION'] = elem.get('swVersion')
                        elem.clear()

                elif event == 'end':
                    elem.clear()
            else:
                elem.clear()
        del context
        return headerDocument

    def fast_iter(self, filePath, familyObj, baseObject, headerDocument):
        context = iter(etree.iterparse(filePath, events=('start', 'end')))
        # get root element
        _, root = next(context)

        tag = ['measInfo', 'granPeriod', 'measType', 'measValue', 'r']

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
                        try:
                            sec = int(re.search(r'^.\w(\d.+?)S', elem.get('duration')).group(1))
                            newDocument['DURATION'] = sec
                        except Exception as e:
                            logger.error(e)
                            newDocument['DURATION'] = elem.get('duration')

                        if self.useEndTime:
                            try:
                                if "{0}{1}".format(sec, newDocument['ENDTIME']) in self.timeCache.keys():
                                    newDocument['BEGINTIME'] = self.timeCache["{0}{1}".format(sec, newDocument['ENDTIME'])]
                                else:
                                    newDocument['BEGINTIME'] = (newDocument['ENDTIME'] - timedelta(0, sec))
                                    # Time cache, used to prevent unneeded beginTime calc
                                    self.timeCache["{0}{1}".format(sec, newDocument['ENDTIME'])] = newDocument['BEGINTIME']
                            except:
                                logger.error("Could not parse end time due to non matching regex with {0}: ".format(newDocument['ENDTIME']))
                        elem.clear()

                    elif elem.tag == namespace + 'measValue':
                        newDocument['MEASOBJLDN'] = newDocument['LOCALDN'] + ',' + re.sub(r', ', ',', elem.get('measObjLdn'))
                        elem.clear()

                elif event == 'end':
                    if elem.tag == namespace + 'measInfo':
                        pass

                    elif elem.tag == namespace + 'measType':
                        measTypes.append(elem.text.upper())
                        pass

                    elif elem.tag == namespace + 'measValue':
                        if len(measValues) != 0:
                            document = copy.deepcopy(newDocument)
                            document['BEGINTIME'] = newDocument['BEGINTIME']
                            document['ENDTIME'] = newDocument['ENDTIME']
                            document.update(dict(zip(measTypes, measValues)))

                            familyObj.setUnitID(self.measInfoId)
                            familyObj.clearDocuments()
                            data_document = {"dataTime": document['BEGINTIME'], "granularitySec": newDocument['DURATION'], "data": document}

                            familyObj.addDocument(data_document)
                            self.nextOp(familyObj=familyObj, baseObject=baseObject)

                        measValues = list()

                    elif elem.tag == namespace + 'r':
                        measValues.append(elem.text)
                        pass

                    elem.clear()
            else:
                elem.clear()
        del context