#!/usr/bin/env python

__version__ = '1.0'

__doc__ = '''
Example file:

BSS release			: 9
Name of BSC			: BSCCBA4
Type of Measurement 		: RT180_Traffic Flow Measurements
Measurement begin date and time	: 2020-04-19 16:00
Measurement end date and time	: 2020-04-19 20:00
Input file name			: /metrica/npa/spool/bss/obsynt/B9/TYPE_180-#-21-#-omccta02m-#-19Apr2020-#-16:00-#-20:00-#-I-#-S.lif
Output file name		: /alcatel/var/share/AFTR/APME/OBSYNT/BSCCBA4/20200419/R18000005.110


CELL_CI_ADJ	CELL_LAC_ADJ	CELL_CI	CELL_LAC	C400	C401	C402
1341	6523	281	26501	108	108	103
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
        self._file_name_regex = re.compile(r'^((?!(R110|R018|RMFS))).+$')
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
            f = open(file_path)
            lines = f.readlines()
            f.close()

            header_data = dict()
            while len(lines) > 0:
                line = lines.pop(0).strip('\n|\r')
                if line == '':
                    break

                # Read file header
                if line.startswith('BSS release'):
                    header_data['BSS_RELEASE'] = line.split(': ')[1].strip()
                elif line.startswith('Name of BSC'):
                    header_data['BSC_NAME'] = line.split(': ')[1].strip()
                elif line.startswith('Type of Measurement'):
                    try:
                        self._command_name = (re.findall(": RT(\d+)", line))[0]
                    except:
                        self._command_name = ''
                elif line.startswith('Measurement begin date and time'):
                    header_data['RESULT_TIME_START'] = line.split(': ')[
                                                           1].strip() + ":00"  # datetime.strptime('{:s}{:s}'.format(line.split(': ')[1].strip(),":00"), '%Y-%m-%d %H:%M:%S')
                elif line.startswith('Measurement end date and time'):
                    header_data['RESULT_TIME_END'] = line.split(': ')[
                                                         1].strip() + ":00"  # datetime.strptime('{:s}{:s}'.format(line.split(': ')[1].strip(),":00"), '%Y-%m-%d %H:%M:%S')

            if self._command_name == '':
                logger.error("ERROR[BSC]: Could not find tableName sample file {0} in read mode.".format(
                    os.path.basename(file_path)))
                return
            header_data['GRANULARITYPERIOD'] = '60'

            column_header = list()

            while len(lines) > 0:
                line = lines.pop(0).strip('\n|\r')
                if line == '':
                    column_header = list()
                    continue

                data = line.replace('?', '').strip()
                if column_header == []:
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
