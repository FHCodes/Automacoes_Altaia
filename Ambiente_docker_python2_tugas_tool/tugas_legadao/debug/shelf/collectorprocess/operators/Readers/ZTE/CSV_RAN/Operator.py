#!/usr/bin/env python
__doc__ = '''
    ZTE RAN Performance CSV Reader
'''

__version__ = '0.1'
__authors__ = [
    "Version 0.1: Rafael Sandes <rafael-s-neiva@openlabs.com.br>"
]

import os
import csv
import importlib
import re
from datetime import datetime, timedelta

# Local libraries
BaseOperator = importlib.import_module("shelf.collectorprocess.operators.BaseOperator").BaseOperator
FamilyObject = importlib.import_module("shelf.collectorprocess.operators.FamilyObject").FamilyObject
logger = importlib.import_module("shelf.collectorprocess.logger").logger

class Operator(BaseOperator):

    # Class Constructor
    def __init__(self, operationParams, baseObject={}):
        BaseOperator.__init__(self, operationParams, baseObject=baseObject)

        self.filename_regex = re.compile(
            r"^UMEID_ITBBU_(?P<UNITID>.*?)_(?P<DATE1>\d{8})_(?P<TIME1>\d{4})-(?P<DATE2>\d{8})_(?P<TIME2>\d{4})"
        )

        self.prefixo = None

    def process(self, familyObj=FamilyObject(), baseObject={}):
        logger.debug("Reading ZTE Inventory CSV file contents...", __file__)
        filePath = familyObj.getFiles()[0]
        familyObj.clearDocuments()

        fileName = os.path.basename(filePath)
        familyObj.fileName = fileName

        interval = 15  # default
        match = self.filename_regex.match(fileName)
        if match:
            try:
                date1, time1 = match.group('DATE1'), match.group('TIME1')
                date2, time2 = match.group('DATE2'), match.group('TIME2')
                self.unit_id = match.group('UNITID')

                dt1 = datetime.strptime(date1 + time1, "%Y%m%d%H%M")
                dt2 = datetime.strptime(date2 + time2, "%Y%m%d%H%M")
                interval = int((dt2 - dt1).total_seconds() / 60)
            except Exception as e:
                # CORRECAO APLICADA AQUI
                logger.error(
                    "Error parsing interval from filename {0}: {1}".format(fileName, e), __file__
                )
        else:
            # CORRECAO APLICADA AQUI
            logger.error(
                "Filename format {0} not expected.".format(fileName), __file__)

        # Mapeamento de tecnologia/prefixo
        tech_map = {
            'ltetdd': 'TDD_',
            'ltefdd': 'FDD_',
            'nbiot':  'NBIOT_',
        }
        lower_path = filePath.lower()
        # encontra a primeira chave presente em filePath, ou '' se nenhuma
        self.prefixo = next(
            (prefix for key, prefix in tech_map.items() if key in lower_path),
            ''
        )

        print(self.prefixo + "AQUIII")

        try:
            with open(filePath, 'r') as f:
                csv_reader = csv.reader(f, delimiter=',')
                headers = next(csv_reader)

                familyObj.setUnitID(self.prefixo+self.unit_id)

                for n_line, row in enumerate(csv_reader):
                    document = {headers[i].upper(): value for i, value in enumerate(row) if i < len(headers)}
                    document["GRANULARITYPERIOD"] = interval

                    try:
                        date_obj = datetime.strptime(document['COLLECTTIME'], "%Y%m%d%H%M%S")
                        document['COLLECTTIME'] = date_obj.strftime("%Y-%m-%d %H:%M:%S")

                        data_time = familyObj.parseEnvelopeDataTime(document["COLLECTTIME"])
                    except (ValueError, KeyError) as e:
                        logger.warning("Could not process row {0} due to {1}".format(n_line, e), __file__)
                        continue


                    familyObj.addDocument({"dataTime": data_time, "granularitySec": int(document["GRANULARITYPERIOD"]),"data": document})
                    self.nextOp(familyObj=familyObj, baseObject=baseObject)
                    familyObj.clearDocuments()

        except Exception as e:
            logger.warning("Unable to process {0} in unit {1} because wrong format => {2}".format(familyObj.fileName, familyObj.getUnitID(), e), __file__)