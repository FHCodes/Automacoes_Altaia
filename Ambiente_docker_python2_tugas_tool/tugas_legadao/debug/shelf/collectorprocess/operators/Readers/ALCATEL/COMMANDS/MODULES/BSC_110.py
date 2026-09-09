#!/usr/bin/env python

__version__ = '1.0'

__doc__ = '''
Example file:

BSS release         : 9
Name of BSC         : BSCCBA4
Type of Measurement         : RT110_Cell TRX Rel Overv Cpt
Measurement begin date and time : 2020-04-19 05:00
Measurement end date and time   : 2020-04-19 06:00
Input file name         : /metrica/npa/spool/bss/obsynt/B9/TYPE_1135-#-21-#-omccta02m-#-19Apr2020-#-05:00-#-06:00-#-A1-#-S.lif and aditional files for TYPE 110
Output file name        : /alcatel/var/share/AFTR/APME/OBSYNT/BSCCBA4/20200419/R11000006.110


BTS_INDEX   BTS_SECTOR  CELL_NAME   CELL_CI CELL_LAC    MC01    MC02    MC02A   MC02B   MC02C   MC02D   MC02E   MC02F   MC02G   MC02H   MC02I   MC03    MC04    MC07    MC10    MC101   MC1040  MC1044  MC1050  MC137   MC138   MC13A   MC13B   MC140A  MC140B  MC141   MC142E  MC142F  MC144E  MC144F  MC147   MC148   MC149   MC14A   MC14C   MC151   MC153   MC15A   MC15B   MC161   MC162   MC170   MC196   MC197   MC24    MC250   MC26    MC27    MC28A   MC29A   MC31    MC320A  MC320B  MC320C  MC320D  MC320E  MC34    MC370A  MC370B  MC380A  MC380B  MC380C  MC380D  MC380E  MC380F  MC381   MC390   MC400   MC41B   MC448A  MC448B  MC449   MC460A  MC461   MC462A  MC462B  MC462C  MC463A  MC463B  MC463C  MC480   MC481   MC541   MC541A  MC551   MC555   MC561   MC586A  MC586B  MC586C  MC607   MC612A  MC612B  MC612C  MC612D  MC621   MC642   MC643   MC645A  MC646   MC647   MC648   MC650   MC652   MC653   MC655A  MC656   MC657   MC658   MC660   MC662   MC663   MC667   MC670   MC671   MC672   MC673   MC674   MC675   MC676   MC677   MC678   MC679   MC701A  MC701B  MC701C  MC701D  MC701E  MC702A  MC702B  MC702C  MC703   MC704A  MC704B  MC705   MC706   MC710   MC711   MC712   MC713   MC714   MC717A  MC717B  MC718   MC736   MC739   MC746B  MC785A  MC785D  MC785E  MC785F  MC800   MC801A  MC801B  MC802A  MC802B  MC803   MC804A  MC804B  MC805A  MC805B  MC81    MC812   MC820   MC821   MC830   MC831   MC850   MC870   MC871   MC8A    MC8B    MC8C    MC8D    MC901   MC902   MC903   MC91    MC921A  MC921B  MC921C  MC921D  MC921E  MC922A  MC922B  MC922C  MC922D  MC922E  MC922F  MC922G  MC922H  MC923A  MC923B  MC923C  MC923D  MC924A  MC924B  MC924C  MC924D  MC924E  MC924F  MC924G  MC924H  MC924I  MC924J  MC924K
9   3   CBA022C 223 26501   0   6   6   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   6   0   0   0   0   0   0   0   0   0   0   0   0   0   14  7   1   0   0   1   4   0   0   0   0   0   0   0   0   0   0   0   0   0   0   6   18  0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   1329    90  14  0   0   0   0   0   0   0   0   0   62  6   1880    0   4   0   4   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0


BTS_INDEX   BTS_SECTOR  CELL_NAME   CELL_CI CELL_LAC    TRXID   MC370A  MC370B  MC380A  MC380B  MC380C  MC380D  MC380E  MC380F  MC381   MC390   MC400   MC621   MC703   MC710   MC711   MC712   MC713   MC714   MC717A  MC717B  MC718   MC736   MC739   MC746B
4   1   CBA028A 281 26501   1   0   0   0   0   0   0   0   0   0   143 659 0   0   0   0   0   0   0   0   0   0   0   0   0


LINK_ID MC350   MC351   MN1_1
16  680 769 3600


MC19    MC35    MC36
0   87  345
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
BaseCommand = importlib.import_module("shelf.collectorprocess.operators.Readers.ALCATEL.COMMANDS.Operator").Command
logger = importlib.import_module("shelf.collectorprocess.logger").logger

# Command class that extends the base command defined in Operator.py
class Command(BaseCommand):

    def __init__(self):
        self._file_name_regex = re.compile(r'^R110.*$')
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
            command_name_list = ['110_COMMONCELL', '110_TRX', '110_N7SIGNALLINGLINK', '110_BSC']
            f = open(file_path)
            lines = f.readlines()
            f.close()

            header_data = dict()
            while len(lines) > 0:
                line = lines.pop(0).strip('\n|\r')
                if line == '':
                    column_header = list()
                    break

                # Read file header
                if line.startswith('BSS release'):
                    header_data['BSS_RELEASE'] = line.split(': ')[1].strip()
                elif line.startswith('Name of BSC'):
                    header_data['BSC_NAME'] = line.split(': ')[1].strip()
                elif line.startswith('Type of Measurement'):
                    self._command_name = '110'
                elif line.startswith('Measurement begin date and time'):
                            header_data['RESULT_TIME_START'] = line.split(': ')[1].strip() + ":00" # datetime.strptime('{:s}{:s}'.format(line.split(': ')[1].strip(),":00"), '%Y-%m-%d %H:%M:%S')
                elif line.startswith('Measurement end date and time'):
                    header_data['RESULT_TIME_END'] = line.split(': ')[1].strip() + ":00" # datetime.strptime('{:s}{:s}'.format(line.split(': ')[1].strip(),":00"), '%Y-%m-%d %H:%M:%S')

            header_data['GRANULARITYPERIOD'] = '60'

            column_header = list()

            while len(lines) > 0:
                line = lines.pop(0).strip('\n|\r')
                if line == '':
                    column_header = list()
                    continue

                data = line.replace('?','').strip()
                if column_header == []:
                    self._command_name = command_name_list.pop(0)
                    column_header = data.upper().split('\t')
                else:
                    data = data.split('\t')
                    if len(column_header) != len(data):
                        logger.error("ERROR[BSC]: Number of values in table {0} of sample {1} is different from number of announced columns.".format(self._command_name, file_name))
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
