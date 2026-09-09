#!/usr/bin/env python

__doc__ = \
    '''
    HUAWEI_COMMANDS_CM files parser manager
'''

__version__ = '1.0'

__authors__ = [
    "Version 1.0: Marco Jeronimo <marco-a-jeronimo@alticelabs.com>"
]

import os
import pkgutil
import re
import time
import importlib
import tarfile
import json
from collections import OrderedDict

# Local libraries
BaseOperator = importlib.import_module("shelf.collectorprocess.operators.BaseOperator").BaseOperator
FamilyObject = importlib.import_module("shelf.collectorprocess.operators.FamilyObject").FamilyObject
logger = importlib.import_module("shelf.collectorprocess.logger").logger
mongoCon = importlib.import_module(
    "shelf.collectorprocess.operators.OutputManagers.Mongo.Operator").mongoConnection


# This class represents a command processor.
class Command(object):

    def __init__(self):
        self._lineSepRegex = re.compile(r'\s{2,}')
        self._startBlockRegex = re.compile(r'^-+[\n|\r]$')
        self._nOfResRegex = re.compile(r'^\(Number of results = \d+\)$')
        self._dataSepRegex = re.compile(r'^(.+?) {2}= {2}(.+?)$')
        self._neNameRegex = re.compile(r' NE Name:(.+?)\*')
        self._commandName = re.compile(r'MML Command:')
        self._cmdName = ''

    @property
    def cmdName(self):
        return self._cmdName

    @staticmethod
    def convert_datestring(s, pattern='%Y-%m-%d %H:%M:%S', out_pattern='%Y-%m-%d %H:%M:%S'):
        try:
            time_string = time.strftime(out_pattern, time.strptime(s[:19], pattern))
        except ValueError:
            raise ValueError("Time string provided ({0}) does not have expected format ({1})".format(s[:19], pattern))
        except TypeError:
            raise TypeError("Time and pattern provided must be a string")

        return time_string

    def parse(self, file_path, lines, mongoConnection):
        logger.debug("Parsing HUAWEI CM command, in file {0}".format(os.path.basename(file_path)))

        line = lines.pop(0).strip('\n|\r|\t')
        try:
            groupName = ''
            documentList = dict()
            toBeContinued = False
            date = ''
            neName = ''
            enodeBName = ''

            while len(lines) > 0 and not line.startswith('========================='):

                if re.search(self._commandName, line) is not  None:
                    line = lines.pop(0).strip('\n|\r|\t')
                    self._cmdName = re.sub(r'[^a-zA-Z0-9_]', '', line.replace(" ", "_"))

                elif line.startswith('+++'):
                    values = re.split(self._lineSepRegex, line.strip())
                    # validar se basta fazer logo o que esta na except
                    try:
                        neName = re.search(self._neNameRegex, values[1]).group(1)
                    except:
                        neName = values[1]

                    try:
                        # obtem o valor do enodeb_name com base no NENAME
                        enodeB = mongoConnection.executeQuery(
                            {"OBJECT": neName, "ENODEB_NAME": {'$exists': True}},
                            'find_one')

                        if 'ENODEB_NAME' in enodeB:
                            enodeBName = enodeB['ENODEB_NAME']
                    except:
                        try:
                            # obtem o valor do genodeb_name com base no NENAME
                            enodeB = mongoConnection.executeQuery(
                                {"OBJECT": neName, "GENODEB_NAME": {'$exists': True}},
                                'find_one')
                            if 'GENODEB_NAME' in enodeB:
                                enodeBName = enodeB['GENODEB_NAME']
                        except:
                            logger.warning("Could not enrich neName: {0} ".format(neName))


                    date = self.convert_datestring(values[2])

                    line = lines.pop(0).strip('\n|\r|\t')

                elif re.search(self._startBlockRegex, lines[0]) is not None:

                    if (toBeContinued and groupName == line) or groupName == '' or groupName == line:
                        groupName = line
                        lines.pop(0)
                        # validate if is header or is column = values
                        if re.search(self._dataSepRegex, lines[0]) is None:
                            header = (lines.pop(0).upper()).strip()
                            header = re.split(self._lineSepRegex, header)
                            lines.pop(0)

                            while len(lines) > 0 and not line.startswith('========================='):
                                line = lines.pop(0).strip('\n|\r|\t')
                                if line in ['', 'To be continued...']:
                                    break
                                elif re.search(self._nOfResRegex, line) is not None:
                                    break
                                else:
                                    # validate if is "NULL" then None
                                    counters = [
                                        None if counter.strip().upper() == 'NULL' else counter.strip()
                                        for counter in re.split(self._lineSepRegex, line.strip())]
                                    try:
                                        document = dict(zip(header, counters))
                                        docKey = document[header[0]]
                                        if docKey not in documentList.keys():
                                            document['DATETIME'] = date
                                            document['NENAME'] = neName
                                            document['ENODEB_NAME'] = enodeBName
                                            document["GRANULARITYPERIOD"] = 1440
                                            documentList[docKey] = document
                                    except Exception as e:
                                        break
                        else:
                            document = dict()
                            line = lines.pop(0).strip('\n|\r|\t')
                            lineParsed = re.search(self._dataSepRegex, line)
                            docKey = lineParsed.group(1).upper().strip()
                            # document[lineParsed.group(1).upper().strip()] = lineParsed.group(2)
                            document[lineParsed.group(1).upper().strip()] = None if lineParsed.group(
                                2).strip().upper() == 'NULL' else lineParsed.group(2).strip()

                            while len(lines) > 0 and not line.startswith('========================='):
                                line = lines.pop(0).strip('\n|\r|\t')
                                if line in ['', 'To be continued...']:
                                    break
                                elif re.search(self._nOfResRegex, line) is not None:
                                    if docKey not in documentList.keys():
                                        document['DATETIME'] = date
                                        document['NENAME'] = neName
                                        document['ENODEB_NAME'] = enodeBName
                                        document["GRANULARITYPERIOD"] = 1440
                                        documentList[docKey] = document
                                    break
                                else:
                                    lineParsed = re.search(self._dataSepRegex, line)
                                    if lineParsed.group(1).upper().strip() not in document.keys():
                                        # document[lineParsed.group(1).upper().strip()] = lineParsed.group(2)
                                        document[lineParsed.group(1).upper().strip()] = None if lineParsed.group(
                                            2).strip().upper() == 'NULL' else lineParsed.group(2).strip()

                        if line.startswith('========================='):
                            break

                    toBeContinued = False
                    isEND = False
                    while len(lines) > 0 and not line.startswith('========================='):
                        if re.search(self._startBlockRegex, lines[0]) is not None:
                            break
                        elif line == 'To be continued...':
                            toBeContinued = True
                            line = lines.pop(0).strip('\n|\r|\t')
                        elif re.search(r'^--- {4}END$', line) is not None:
                            isEND = True
                            line = lines.pop(0).strip('\n|\r|\t')
                            break
                        else:
                            line = lines.pop(0).strip('\n|\r|\t')

                    if line.startswith('=========================') or (isEND and not toBeContinued):
                        break
                else:
                    line = lines.pop(0).strip('\n|\r|\t')
            # Validate if can return list of documents
            for docKey in documentList.keys():
                yield documentList[docKey]

        except IOError:
            logger.error("Could not open sample file {0} in read mode.".format(os.path.basename(file_path)))


class Operator(BaseOperator):

    # Class Constructor
    def __init__(self, operationParams, baseObject={}):
        BaseOperator.__init__(self, operationParams, baseObject=baseObject)

        config = json.load(open('/opt/alticelabs/namf/src/shelf/collectorprocess/config/mongo_enrich_config.json'))
        config.update(
            json.load(open('{0}/{1}/config.json'.format(config['location'], self.options['enrich'].replace('.', '/'))), object_pairs_hook=OrderedDict))

        self._mongoConnection = mongoCon(config)
        self._mongoConnection.getConnection()

        self.filename_regex = re.compile(r'^MMLTask_(?P<COMMAND_NAME>.*)_\d{8}_(\d{6})\.txt$')
        # Available commands list and filenames
        self._command = Command()

    def process(self, familyObj=FamilyObject(), baseObject={}):

        # Get the files to parse
        files_to_process = familyObj.getFiles()

        logger.debug("Entering Commands files parser manager")

        for file_path in files_to_process:
            familyObj.clearDocuments()

            # Get file's name to find the command
            familyObj.fileName = os.path.basename(file_path)
            filePath = ''
            removeFile = False

            try:
                # Open file for writing
                if file_path.endswith(".tar.gz"):
                    removeFile = True
                    # Create a hidden, temporary file name without the .gz extension
                    fileDir = os.path.dirname(file_path)
                    tmp = os.path.basename(file_path).replace('.tar.gz', '.txt')
                    filePath = os.path.join(fileDir, tmp)

                    tar = tarfile.open(file_path, "r:gz")
                    tar.extract(tmp, fileDir)
                    tar.close()

                    if os.path.exists(filePath):
                        if os.path.getsize(filePath) == 0:
                            raise IOError("The file \"{}\" dont have data".format(file_path))
                    else:
                        logger.warning("Could not create a hidden file \"{}\" in read mode: ".format(file_path))
                        return
            except IOError:
                logger.warning("Could not open sample file \"{}\" in read mode: ".format(file_path), __file__)
                return

            if filePath == '':
                filePath = file_path

            f = open(filePath)
            lines = f.readlines()
            f.close()

            command = self._command
            familyName = self.filename_regex.match(familyObj.fileName).group("COMMAND_NAME")

            while lines:
                lines.pop(0).strip('\n|\r|\t')
                try:
                    for document in command.parse(file_path, lines, self._mongoConnection):
                        if command.cmdName == '':
                            familyObj.setUnitID(familyName)
                        else:
                            familyObj.setUnitID(command.cmdName)
                        try:
                            data_time = familyObj.parseEnvelopeDataTime(document["DATETIME"])
                        except ValueError as e:
                            logger.warning("Could not build mediationEnvelope due to {0}: ".format(e), __file__)
                            continue

                        familyObj.addDocument({"dataTime": data_time, "granularitySec": document["GRANULARITYPERIOD"], "data": document})

                        # Final operations to the fields with timestamp and granularity period
                        self.nextOp(familyObj=familyObj, baseObject=baseObject)
                        familyObj.clearDocuments()
                except (ValueError, TypeError, IOError) as e:
                    logger.error(e)

            if removeFile:
                os.remove(filePath)
