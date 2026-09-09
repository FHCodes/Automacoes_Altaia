__version__ = '1.0'

__doc__ = '''
    Oracle DSR (Diameter Signaling Router) Performance Reader
'''

__authors__ = [
	"Version 1.0: paulo-a-gil <paulo-a-gil@alticelabs.com>"
]

import os
import re
import csv
import importlib
import subprocess
from datetime import datetime

# Local libraries
BaseOperator = importlib.import_module("shelf.collectorprocess.operators.BaseOperator").BaseOperator
FamilyObject = importlib.import_module("shelf.collectorprocess.operators.FamilyObject").FamilyObject
logger = importlib.import_module("shelf.collectorprocess.logger").logger

class Operator(BaseOperator):

    # Class constructor
    def __init__(self, operationParams, baseObject={}):
        BaseOperator.__init__(self, operationParams, baseObject=baseObject)
        self._baseDocument = dict()
        self._unit = None
        self._measType = None

    def process_value(self, value):
        if "=" in value:
            valueRegex = re.compile(r'=(?P<NUM>\d+)/(?P<DEN>\d+)').match(value)
            value = round(float(valueRegex.group('NUM'))/float(valueRegex.group('DEN')), 2)
        elif 'n/a' in value:
            value = ''

        return value

    def process_document(self, familyObject, baseObject, document):
        document.update(self._baseDocument)

        try:
            data_time = familyObject.parseEnvelopeDataTime(document["STARTTIME"])
        except ValueError as e:
            logger.warning("Could not build mediationEnvelope due to {0}: ".format(e), __file__)

        familyObject.addDocument({"dataTime": data_time, "granularitySec": int(document["GRANULARITYPERIOD"]*60), "data": document})
        self.nextOp(familyObj=familyObject, baseObject=baseObject)
        familyObject.clearDocuments()

    def process(self, familyObj=FamilyObject(), baseObject={}):
        logger.debug("Reading ORACLE DSR Performance CSV file' contents...", __file__)
        filesToProcess = familyObj.getFiles()
        familyObj.clearDocuments()

        for filePath in filesToProcess:
            # If file is empty, bota fora :)
            if os.path.getsize(filePath) == 0:
                logger.warning("File {0} is empty.".format(os.path.basename(filePath)), __file__)
                continue

            # Get file's name
            fileName = os.path.basename(filePath)
            familyObj.fileName = fileName

            """
            Run a subprocess to sort the file on the filesystem
            Since Arrayed files contain the entity/object inside square brackets (ex: IcRateAvg[deapic301_ams_01_syn]),
            simply call sort command using [ as a delimiter. Data will be sorted according to the rightmost part of the [ char

            Command:
            sort -o <file> -V -t [ -k 2,2 <file>

            Flags:
            -o, --output=FILE
            -k, --key=KEYDEF
            -t, --field-separator=SEP
            -V, --version-sort
            """

            try:
                cmd = ["sort", "-o", filePath, "-V", "-t", "[", "-k", "2,2", filePath]
                process = subprocess.Popen(cmd, stdout=subprocess.PIPE)
                output, error = process.communicate()
            except:
                logger.error("An error occured when calling subprocess on the file {0}: {1}".format(fileName, error), __file__)
                logger.error("Subprocess output: ".format(output), __file__)
                continue

            # Get info from filename
            fnameRegex = re.compile(r'^(?P<server>[^_]+)_(?P<unit>.+)_s(?P<starttime>\d+)_e(?P<endtime>.+)_c(?P<controltime>\d+)\.csv$')
            fnameRegex = fnameRegex.match(fileName)

            # Format startTime and endTime
            self._baseDocument["STARTTIME"] = datetime.strftime(datetime.strptime(fnameRegex.group('starttime'), "%Y%m%d%H%M"), "%Y-%m-%d %H:%M:%S")
            self._baseDocument["ENDTIME"] = datetime.strftime(datetime.strptime(fnameRegex.group('endtime'), "%Y%m%d%H%M"), "%Y-%m-%d %H:%M:%S")

            # Set granularity field
            self._baseDocument["GRANULARITYPERIOD"] = 15

            # Get UnitID from filename
            self._unit = fnameRegex.group('unit').upper()

             # Set Unit ID
            familyObj.setUnitID(self._unit)

            # Open the file in reading mode
            try:
                f = open(filePath, 'r')
            except IOError:
                logger.error("Could not open sample file \"{0}\" in read mode: ".format(fileName), __file__)

            # Set measurement type
            self._measType = "MeasArrayed"
            if "MEASSIMPLE" in self._unit or "SINGLE" in self._unit:
                self._measType = "MeasSimple"

            # Init variables
            object = ""
            document = dict()

            # Try parsing CSV file
            try:
                for line in csv.reader(f):
                    # Skip empty line
                    if not line:
                        continue

                    # Get server name
                    if "=NODE=" in line[0]:
                        self._baseDocument["SERVER"] = line[1]
                        continue

                    # Ignore header line
                    if "Measurement Name" in line[0]:
                        continue

                    # Handle Object line only for files of type MeasArrayed
                    # Get object from counter name if measurement type is Measarrayed
                    if self._measType == "MeasArrayed":
                        objRegex = re.compile(r'^.+(?P<object>\[.+\])').match(line[0])

                        if not object:
                            object = objRegex.group('object')
                            document["OBJECT"] = objRegex.group('object').replace("[","").replace("]","")
                        elif object != objRegex.group('object'):
                            # If object is different, it belongs to another set of measurements
                            # In thant case, process document
                            self.process_document(familyObj, baseObject, document)

                            # Reset document dict
                            document = dict()

                            # Get object name from counter name regex
                            object = objRegex.group('object')
                            document["OBJECT"] = objRegex.group('object').replace("[","").replace("]","")

                    """
                    Process counter name

                    If measurement type is MeasArrayed, the counter has the format:
                    => counterName[objectName]
                    Else, if measurement type is Single, the format is:
                    => counterName
                    """
                    counter = line[0]
                    counter = counter.replace(object, "").upper()

                    """
                    Process value

                    If value has the format =<int>/<int>, conversion is needed
                    Else, if the value is n/a, convert to null:
                    """
                    value = line[3]
                    document[counter] = self.process_value(value)

            except Exception as e:
                logger.warning("Unable to process file {0} because => {1}".format(familyObj.fileName, e), __file__)
                continue

            # If measurement type is Single, event is processed after EOF
            # If measurement type is Arrayed, the last event is processed after EOF
            if document:
                self.process_document(familyObj, baseObject, document)
