#!/usr/bin/env python

__doc__ = \
'''
    Italtel 3GPP 32.435 Generic Performance XML Reader
'''

__version__ = '1.0'

__authors__ = [
    "Version 1.0: Paulo Gil <paulo-a-gil@alticelabs.com>"
]

# Native libraries
import os
import re
import sys
import json
import copy
import shlex
from datetime import datetime
import xml.etree.cElementTree as etree
import importlib

# # Local libraries
BaseOperator = importlib.import_module("shelf.collectorprocess.operators.BaseOperator").BaseOperator
FamilyObject = importlib.import_module("shelf.collectorprocess.operators.FamilyObject").FamilyObject
logger = importlib.import_module("shelf.collectorprocess.logger").logger

def convertTimeZone(date):
    if '-' in date:
        d1 = datetime.strptime(date[:-10], '%Y-%m-%dT%H:%M:%S')
        d2 = datetime.strptime('0001-01-01 ' + date[-5:] + ':00', '%Y-%m-%d %H:%M:%S')
        t1 = datetime.strptime('0001-01-01 00:00:00', '%Y-%m-%d %H:%M:%S')
        return t1 + (d1 - d2)
    return datetime.strptime(date, '%Y-%m-%dT%H:%M:%S')

class Operator(BaseOperator):

    # Class Constructor
    def __init__(self, operationParams, baseObject={}):
        BaseOperator.__init__(self, operationParams, baseObject=baseObject)

        self._datetime_regex = re.compile(r'^(?P<datetime>\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}).*$')

        # Sets the interval unit, as default its defined to Minutes
        self._intervalUnit = 'M'
        if "intervalUnit" in self.options:
            self._intervalUnit = self.options["intervalUnit"].upper()

        # Sets the interval unit, as default its defined to Minutes
        self._convertTimeZone = True
        if "convertTimeZone" in self.options:
            self._convertTimeZone = (False if self.options["convertTimeZone"].upper() == 'FALSE' else True)

        # Sets configuration file from self.options
        if "config" not in self.options:
            logger.warning('Missing flag "config" in spec, using generic configuration!')
            self.options["config"] = "generic"

        self._config = json.load(open('/opt/alticelabs/namf/src/shelf/collectorprocess/operators/Readers/ITALTEL/3GPP/32_435/config/{0}.json'.format(self.options["config"])))
        self._regex = re.compile(self._config['regex'])

        self.measInfoId = ''

    def process(self, familyObj=FamilyObject(), baseObject={}):

        filesToBeProcessed = familyObj.getFiles()
        familyObj.clearFiles()

        for filePath in filesToBeProcessed:

            fileName = os.path.basename(filePath)
            familyObj.fileName = fileName

            logger.debug("[Reader] Reading Italtel Performance 3GPP 32.435 XML files '{0}' contents...".format(fileName), __file__)

            if os.path.getsize(filePath) == 0:
                logger.warning("File {0} is empty.".format(fileName), __file__)
                continue

            self.fast_iter(filePath, familyObj, baseObject)

    def fast_iter(self, filePath, familyObj, baseObject):
        context = iter(etree.iterparse(filePath, events=('start', 'end')))
        # get root element
        _, root = next(context)

        tag = list()

        for elem in self._config:
            if elem != 'regex':
                try:
                    for t in self._config[elem]['tags']:
                        tag.append(t)
                        for attr in self._config[elem]['tags'][t]['attrs']:
                            tag.append(attr)
                except:
                    pass

        if isinstance(tag, list):
            multi = True
        else:
            multi = False

        sharedDoc = dict()
        document = dict()
        namespace = None

        for event, elem in context:
            if event == 'start' and namespace is None:
                if "}" in elem.tag:
                    namespace = elem.tag.split("}")[0].strip("{")
                    namespace = "{" + namespace + "}"
                else:
                    namespace = ""

            elem.tag = elem.tag.replace(namespace, '')

            if multi:
                if event == 'start':
                    if elem.tag == 'measType':
                        if elem.text:
                            measTypes.append(elem.text.upper())
                        continue

                    elif elem.tag == 'measTypes':
                        if elem.text:
                            measTypes = (elem.text.upper()).split(' ')
                        continue

                    elif elem.tag == 'measResults':
                        if elem.text:
                            measValues = shlex.split(elem.text)
                            measValues = [None if value == 'NIL' else value for value in measValues]

                    elif elem.tag == 'measInfo':
                        if 'measInfoId' in tag:
                            self.measInfoId = elem.get('measInfoId').upper()
                        else:
                            self.measInfoId = ''

                        document = copy.deepcopy(sharedDoc)
                        measTypes = dict()
                        measValues = dict()
                        elem.clear()
                        continue

                    elif elem.tag == 'measValue':
                        if 'measValue' in tag:
                            document['MEASOBJLDN'] = elem.get('measObjLdn')
                        elem.clear()
                        continue

                    for key in elem.attrib.keys():
                        if key in tag:

                            header = self._config['header']['tags']

                            try:
                                objects = self._config['object']['tags']
                            except:
                                objects = []
                                pass

                            if elem.tag in objects:
                                if key in objects[elem.tag]['attrs']:
                                    for obj in objects[elem.tag]['attrs'][key]:
                                        if obj not in document:
                                            if key in ['duration', 'endTime']:
                                                # Format duration field
                                                if key == 'duration':
                                                    document['DURATION'] = self.format_interval(int(FamilyObject.parseEnvelopeGranularitySec(elem.get('duration'))), elem.get('duration')[-1:], self._intervalUnit)

                                                # Format endTime field
                                                elif key == 'endTime':
                                                    if self._convertTimeZone:
                                                        document['ENDTIME'] = datetime.strftime(convertTimeZone(elem.get('endTime')), '%Y-%m-%d %H:%M:%S')
                                                    else:
                                                        document['ENDTIME'] = elem.get('endTime')[:-10].replace('T', ' ')
                                            else:
                                                document[obj] = elem.get(key)

                            elif elem.tag in header:
                                if key in header[elem.tag]['attrs']:
                                    for obj in header[elem.tag]['attrs'][key]:
                                        if obj not in sharedDoc:
                                            # Special key fields that need formatting
                                            # Format beginTime field
                                            if key == 'beginTime':
                                                if self._convertTimeZone:
                                                    sharedDoc['BEGINTIME'] = datetime.strftime(convertTimeZone(elem.get('beginTime')), '%Y-%m-%d %H:%M:%S')
                                                else:
                                                    sharedDoc['BEGINTIME'] = elem.get('beginTime')[:-10].replace('T', ' ')
                                            else:
                                                sharedDoc[obj] = elem.get(key)
                elif event == 'end':

                    if elem.tag == 'measValue':
                        if self.measInfoId == '':
                            if 'MEASINFOID' in document:
                                self.measInfoId = document['MEASINFOID']
                            else:
                                self.measInfoId = document['JOBID']

                        if self.measInfoId != '':
                            document['MEASUREMENTDATAOBJECT'] = familyObj.fileName.replace('.xml','')
                            value = re.sub(self._regex, '', self.measInfoId)

                            if value != '':
                                self.measInfoId = value

                            familyObj.setUnitID(self.measInfoId)
                            familyObj.clearDocuments()

                            document.update(dict(zip(measTypes, measValues)))

                            try:
                                data_time = FamilyObject.parseEnvelopeDataTime(document['BEGINTIME'])
                            except ValueError as e:
                                logger.warning( "Could not build mediationEnvelope due to : {0}".format(e), __file__)
                                continue

                            data_document = {"dataTime": data_time, "granularitySec": self.format_interval(document['DURATION'], self._intervalUnit, 'S'), "data": document}
                            familyObj.addDocument(data_document)
                            self.nextOp(familyObj=familyObj, baseObject=baseObject)

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
