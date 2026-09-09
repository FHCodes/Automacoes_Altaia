__version__ = '1.0'

__doc__ = '''
    Cisco vEPC (Embedded Packet Capture) Performance Reader
'''

__authors__ = [
	"Version 1.0: paulo-a-gil <paulo-a-gil@alticelabs.com>"
]


import re
import os
import csv
import copy
import importlib
from datetime import datetime, timedelta


# Local libraries
BaseOperator = importlib.import_module("shelf.collectorprocess.operators.BaseOperator").BaseOperator
FamilyObject = importlib.import_module("shelf.collectorprocess.operators.FamilyObject").FamilyObject
logger = importlib.import_module("shelf.collectorprocess.logger").logger


class Operator(BaseOperator):


    # Class constructor
    def __init__(self, operationParams, baseObject={}):
        BaseOperator.__init__(self, operationParams, baseObject=baseObject)
        self._bsconfig = dict()
        self._epc_name = None
        self._bscfg_path = None
        self._documentUnitId = None
        self._translateUnitId = {"RULEBASE": "ECSRBASE"}

        # Get bsconfig folder path from options
        if "bsconfig_path" in self.options:
            self._bscfg_path = self.options["bsconfig_path"]
            self._bscfg_path = self._bscfg_path.replace("{{ip_omc}}", baseObject.args.sourceId)
        else:
            logger.error("BSCONFIG path is not present in self.options! Aborting...", __file__)
            return


    '''
    Returns a dict with the information from BSCONFIG file.

            Parameters:
                    bsconfig_filename (str): BSCONFIG file name

            Returns:
                    bsconfig_data (dict): Dictionary with BSCONFIG parsed data
    '''
    def process_bsconfig(self, bsconfig_filename):
        bsconfig_data = dict()

        # Check if provided bsconfig folder exists
        if os.path.exists(self._bscfg_path):
            # os.path.join to form the path to BSCONFIG file
            bscfg_file = os.path.join(self._bscfg_path, bsconfig_filename)
            # Check if BSCONFIG file exists
            if os.path.exists(bscfg_file):
                # Read BSCONFIG File
                for line in open(bscfg_file, "r"):
                    # Apply regex to parse lines and extract unit and header information
                    headerRegex = re.compile(r'(?P<unit>\S+) schema (?P<schema>\S+) format (?P<header>.+)').match(line.strip())

                    if headerRegex:
                        unit = headerRegex.group('unit')
                    else:
                        # Extra regex to parse "system" related headers
                        headerRegex = re.compile(r'schema system\S+ format (?P<header>.+)').match(line.strip())

                        if headerRegex:
                            unit = "system"
                        else:
                            continue

                    # Get header and corresponding EMS name
                    header = headerRegex.group('header').replace("%","")
                    ems = header.split(",")[1]

                    # Add extracted information to return dict
                    if unit not in bsconfig_data.keys():
                        bsconfig_data[ems.upper()] = dict()

                    bsconfig_data[ems]["unit"] = unit
                    bsconfig_data[ems]["header"] = [item.upper() for item in header.split(",")]
                    del bsconfig_data[ems]["header"][1]

        return bsconfig_data


    # Process document to NAMF Mediation Envelope
    def process_document(self, familyObject, baseObject, document):
        # Set Unit ID
        familyObject.setUnitID(self._documentUnitId)

        # Add EPC_NAME and GRANULARITYPERIOD to document
        document["EPC_NAME"] = self._epc_name
        document["GRANULARITYPERIOD"] = 15

        # Parse DATETIME
        document["DATETIME"] = datetime.strptime("{0}{1}".format(document["DATE"], document["TIME"]), "%Y%m%d%H%M%S")
        document["DATETIME"] = document["DATETIME"] - timedelta(minutes=15)
        document["DATETIME"] = datetime.strftime(document["DATETIME"], "%Y-%m-%d %H:%M:%S")

        # Parse envelope DataTime
        try:
            data_time = familyObject.parseEnvelopeDataTime(document["DATETIME"])
        except ValueError as e:
            logger.warning("Could not build mediationEnvelope due to {0}: ".format(e), __file__)
            return

        # Proceed with mediation envelope
        familyObject.addDocument({"dataTime": data_time, "granularitySec": int(document["GRANULARITYPERIOD"]*60), "data": document})
        self.nextOp(familyObj=familyObject, baseObject=baseObject)
        familyObject.clearDocuments()


    def process(self, familyObj=FamilyObject(), baseObject={}):
        logger.debug("Reading CISCO EPC Performance BSCONFIG file' contents...", __file__)
        filePath = familyObj.getFiles()[0]
        familyObj.clearDocuments()

        # If file is empty, bota fora :)
        if os.path.getsize(filePath) == 0:
            logger.warning("File {0} is empty.".format(os.path.basename(filePath)), __file__)
            return

        # Get file's name
        fileName = os.path.basename(filePath)
        familyObj.fileName = fileName

        # Get BSCONFIG and EPC name from bulkstat filename
        fileNameRegex = re.compile(r"bulkstat_(?P<bscfg>\S+)_\d+.*").match(fileName)
        bscfg_name = "BSCFG_{0}.cfg".format(fileNameRegex.group('bscfg'))
        self._epc_name = re.compile(r"\d+_(?P<epc_name>\S+)").match(fileNameRegex.group('bscfg')).group('epc_name')

        # Parse correspondig BSCONFIG file and get a dict with parsed data
        self._bsconfig = self.process_bsconfig(bscfg_name)

        # Check if BSCONFIG file was successfully processed
        if not self._bsconfig:
            logger.error("Could not parse BSCONFIG file \"{0}\": either file is corrupted or path does not exists".format(bscfg_name), __file__)
            return

        # Open the bulkstat file in reading mode
        try:
            f = open(filePath, 'r')
        except IOError:
            logger.error("Could not open sample file \"{0}\" in read mode: ".format(fileName), __file__)

        # Initialize parsing variables
        document = dict()
        lastKeyNumber = None

        try:
            for line in csv.reader(f):
                # Check if line has valid column items
                if "%" in ",".join(line):
                    continue

                if line[0] == "EMS":
                    key = line[1]

                    # Check if EMS name exists in BSCONFIG
                    if key in self._bsconfig.keys():
                        # Process header and line safely by deepcopying it's source
                        header = copy.deepcopy(self._bsconfig[key]["header"])
                        line = copy.deepcopy(line)

                        # Delete unwanted value in line
                        del line[1]

                        # Check if the length of the header matches with the length of the sample file
                        if len(header) != len(line):
                            logger.warning("Number of values in current line is different than number of announced columns in sample".format(fileName))
                            continue

                        # Get unitID
                        currentUnitId = self._bsconfig[key]["unit"]
                        currentUnitId = currentUnitId.upper()

                        # Get the header format number associated with the BSCONFIG key
                        if currentUnitId in self._translateUnitId:
                            keyNumber = key.replace(self._translateUnitId[currentUnitId],"")
                        else:
                            keyNumber = key.replace(currentUnitId,"")

                        if (self._documentUnitId and currentUnitId != self._documentUnitId) or (lastKeyNumber and keyNumber == "1"):
                            self.process_document(familyObj, baseObject, document)
                            document = dict()

                        # Create a temporary document that contains the zip between the current header and current line
                        tempDocument = dict(zip(header,line))

                        # Update document using tempDocument as base
                        for k,v in tempDocument.iteritems():
                            if k not in document.keys():
                                document.update({k:v})

                        self._documentUnitId = currentUnitId
                        lastKeyNumber = keyNumber
                    else:
                        logger.warning("EMS not found in BSCONFIG file \"{}\" in read mode: ".format(bscfg_name), __file__)
                        continue

            # The last document is processed outside the for loop since the processing is shifted ahead by one
            self.process_document(familyObj, baseObject, document)

        except Exception as e:
            logger.warning("Unable to process file {0} because => {1}".format(familyObj.fileName, e), __file__)
            return
