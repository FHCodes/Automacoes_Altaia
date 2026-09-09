#!/usr/bin/env python

__version__ = '1.0'

__doc__ = '''
Example file:

BSS release		 : 9
Name of BSC		 : BSCCBA3
Type of Measurement		 : RT18_A & Abis Interface Analy
Measurement begin date and time : 2019-09-12 04:00
Measurement end date and time   : 2019-09-12 05:00
Input file name		 : /metrica/npa/spool/bss/obsynt/B9/TYPE_18-#-20-#-omccta02m-#-12Sep2019-#-04:00-#-05:00-#-I-#-S.lif
Output file name		: /alcatel/var/share/AFTR/APME/OBSYNT/BSCCBA3/20190912/R01800005.255


C180A   C180B   C180C   C180D   C180E   C181A   C181B   C181C   C181D   C181E   C181F   C181G   C181H   C181I   C181J   C181K   C181L   C182
0   0   0   49  0   0   0   0   0   0   0   1   0   0   0   0   0   1


LINK_ID C750	C751
1   0   0
'''

__authors__ = [
    "Version 1.0: bruno-e-silva <bruno-e-silva@alticelabs.com>"
]

import os
import re
import copy
import importlib

# Local libraries
BaseOperator = importlib.import_module("shelf.collectorprocess.operators.BaseOperator").BaseOperator
FamilyObject = importlib.import_module("shelf.collectorprocess.operators.FamilyObject").FamilyObject
BaseCommand = importlib.import_module(
    "shelf.collectorprocess.operators.Readers.ALCATEL.COMMANDS.Operator").Command
logger = importlib.import_module("shelf.collectorprocess.logger").logger


# Command class that extends the base command defined in Operator.py
class Command(BaseCommand):

    def __init__(self):
        self._file_name_regex = re.compile(r'^R018.*$')
        self._command_name = ''
        self._lineSepRegex = re.compile(r'\t')

    @property
    def line_format(self):
        return self._line_format

    def parse(self, file_path):
        logger.debug("Parsing BSC format, in file {0}".format(os.path.basename(file_path)))

        file_name = os.path.basename(file_path)

        # Open file for reading
        try:
            command_name_list = ['18_BSC', '18_AINTERFACECHANNEL']
            f = open(file_path)
            lines = f.readlines()
            f.close()

            header_data = dict()
            while len(lines) > 0:
                line = lines.pop(0).strip('\n|\r')
                if line == '':
                    column_header = list()
                    break

                # Read  file header
                if line.startswith('BSS release'):
                    header_data['BSS_RELEASE'] = line.split(': ')[1].strip()
                elif line.startswith('Name of BSC'):
                    header_data['BSC_NAME'] = line.split(': ')[1].strip()
                elif line.startswith('Type of Measurement'):
                    self._command_name = '18'
                elif line.startswith('Measurement begin date and time'):
                    header_data['RESULT_TIME_START'] = line.split(': ')[
                                                          1].strip() + ":00"  # datetime.strptime('{:s}{:s}'.format(line.split(': ')[1].strip(),":00"), '%Y-%m-%d %H:%M:%S')
                elif line.startswith('Measurement end date and time'):
                    header_data['RESULT_TIME_END'] = line.split(': ')[
                                                        1].strip() + ":00"  # datetime.strptime('{:s}{:s}'.format(line.split(': ')[1].strip(),":00"), '%Y-%m-%d %H:%M:%S')

            header_data['GRANULARITYPERIOD'] = '60'

            column_header = list()

            while len(lines) > 0:
                line = lines.pop(0).strip('\n|\r')
                if line == '':
                    column_header = list()
                    continue

                data = line.replace('?', '').strip()
                if column_header == []:
                    self._command_name = command_name_list.pop(0)
                    column_header = data.upper().split('\t')
                else:
                    data = data.split('\t')
                    if len(column_header) != len(data):
                        logger.error(
                            "ERROR[BSC]: Number of values in table {0} of sample {1} is different from number of announced columns.".format(
                                self._command_name, file_name))
                        continue
                    document = copy.deepcopy(header_data)
                    document.update(dict(zip(column_header, data)))

                    try:
                        # Parse the date
                        data_time = FamilyObject.parseEnvelopeDataTime(header_data['RESULT_TIME_START'])
                    except ValueError as e:
                        logger.error(
                            "Could not build mediationEnvelope due to {0}: ".format(
                                e), __file__)
                        continue

                    yield {"dataTime": data_time, "granularitySec": "60", "data": document}

        except IOError:
            logger.error("ERROR[BSC]: Could not open sample file {0} in read mode.".format(os.path.basename(file_path)))
