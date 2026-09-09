__version__ = "1.1"

__doc__ = """
    HUAWEI OSS VAS WAD Performance CSV Reader
"""

__authors__ = [
	"Version 1.1: paulo-a-gil <paulo-a-gil@alticelabs.com>"
]

import re
import os
import json
import importlib
from csv import reader
from subprocess import call
from datetime import datetime, timedelta

# Local libraries
BaseOperator = importlib.import_module("shelf.collectorprocess.operators.BaseOperator").BaseOperator
FamilyObject = importlib.import_module("shelf.collectorprocess.operators.FamilyObject").FamilyObject
logger = importlib.import_module("shelf.collectorprocess.logger").logger
mongoCon = importlib.import_module("shelf.collectorprocess.operators.OutputManagers.Mongo.Operator").mongoConnection

class Operator(BaseOperator):
    # Class constructor
    def __init__(self, operationParams, baseObject={}):
        BaseOperator.__init__(self, operationParams, baseObject=baseObject)

        self._mongoConnection = mongoCon(json.load(open("/opt/alticelabs/namf/src/shelf/collectorprocess/config/mongo_config.json")))
        self._unitMapping = json.load(open("/opt/alticelabs/namf/src/shelf/collectorprocess/operators/Readers/HUAWEI/CSV/VAS/WAD/unitMapping.json"))
        self._neMapping = json.load(open("/opt/alticelabs/namf/src/shelf/collectorprocess/operators/Readers/HUAWEI/CSV/VAS/WAD/neMapping.json"))
        self._ip_omc = baseObject.args.sourceId
        self._collector = "_".join([baseObject.args.vendor, baseObject.args.model])

    def process(self, familyObj=FamilyObject(), baseObject={}):
        logger.debug("Reading HUAWEI OSS VAS WAD Performance CSV file\' contents...", __file__)
        filesToProcess = familyObj.getFiles()
        self._mongoConnection.getConnection()

        for filePath in filesToProcess:
            familyObj.clearDocuments()
            originalFilePath = filePath

            fileName = os.path.basename(filePath)
            familyObj.fileName = fileName

            # Flag to indicate if we need to remove file at the end of each parsed file
            removeFile = False

            # Try gunzip the file
            try:
                # Open file for writing
                if os.path.splitext(originalFilePath)[1] == ".gz":
                    removeFile = True
                    # Create a hidden, temporary file name without the .gz extension
                    fileDir = os.path.dirname(originalFilePath)
                    fileName = "."  + os.path.basename(originalFilePath)
                    fileName = os.path.splitext(fileName)[0]
                    filePath = os.path.join(fileDir, fileName)

                    fOut = open(filePath, "w")
                    call(["gunzip", "-c", originalFilePath], stdout=fOut)

                    fOut.close()

                    if os.path.exists(filePath)==True:
                        if os.path.getsize(filePath) == 0:
                            os.remove(filePath)
                            raise IOError("")
                    else:
                        logger.warning("Could not create a hidden file \"{}\" in read mode: ".format(filePath))
                        continue
            except IOError:
                logger.warning("Could not open sample file \"{}\" in read mode: ".format(filePath), __file__)
                continue

            # If file is empty, bota fora :)
            if os.path.getsize(filePath) == 0:
                logger.warning("File {0} is empty.".format(fileName), __file__)
                continue

            # Try opening the file
            try:
                f = open(filePath, "r")
            except IOError:
                logger.error("Could not open file \"{0}\" in read mode.".format(fileName), __file__)

            # Get datetime from filename and get unit info from mapping
            fileNameRegex = re.match("^.(?P<unit>(resultado|telcomanager_wad))_script_(?P<datetime>\d{8}_\d{6}).*$", os.path.basename(filePath))
            fileDateTime = datetime.strptime(fileNameRegex.group("datetime"), "%Y%m%d_%H%M%S")
            unitInfo = self._unitMapping[fileNameRegex.group("unit").upper()]

	        # Execute mongo query to return current and last day data
            queryDay = {"collector": self._collector, "eventDate": datetime.strftime(fileDateTime, "%Y-%m-%d"), "ip": self._ip_omc}
            queryResultDay = self._mongoConnection.executeQuery(queryDay, "find")
            queryLastDay = {"collector": self._collector, "eventDate": datetime.strftime((fileDateTime - timedelta(days=1)), "%Y-%m-%d"), "ip": self._ip_omc}
            queryResultLastDay = self._mongoConnection.executeQuery(queryLastDay, "find")

            # Create lists with datetimes stored in Mongo for the present and last days
            currentDaySavedDatetimes = [datetime.strptime(datetime.strftime(fileDateTime, "%Y-%m-%d") + " " + item["eventTime"], "%Y-%m-%d %H:%M:%S") for item in list(queryResultDay)]
            lastDaySavedDatetimes = [datetime.strptime(datetime.strftime((fileDateTime - timedelta(days=1)), "%Y-%m-%d") + " " + item["eventTime"], "%Y-%m-%d %H:%M:%S") for item in list(queryResultLastDay)]

            # Select datetimes from sample file if unitId is CAMPAIGNMANAGE and ignore last 2 hours of data
            datetimes = sorted(list(set([datetime.strptime(line[1].replace(" ",""), unitInfo["format"]) for nLine, line in enumerate(reader(f, delimiter=";")) if unitInfo["unitID"] == "CAMPAIGNMANAGE" and nLine != 0 and (fileDateTime - datetime.strptime(line[1].replace(" ",""), unitInfo["format"])) > timedelta(0, 2*60*60)])))

            # Check previous selected datetimes if they are newer than the last processed datetime saved in Mongo
            processEventDatetimes = [dt for dt in datetimes if dt not in (currentDaySavedDatetimes+lastDaySavedDatetimes)]

	    	# Set FamilyObj unit ID
            familyObj.setUnitID(unitInfo["unitID"])

            # Get granularity and network element name from unit info
            granularity = unitInfo["granularity"]
            ne = self._neMapping[self._ip_omc]

            # Get the corresponding header from unit info
            header = unitInfo["header"]

            # Rewind csv file
            f.seek(0)

            # Document variable initialization
            document = dict()
            updateMongo = False

            try:
                for nLine, line in enumerate(reader(f, delimiter=";")):
                    # Skip first line to ignore file header
                    if nLine == 0:
                        continue

                    # Skip empty lines
                    if not line:
                        continue

                    # Checks if the length of the header equals the length of the line
                    if len(header) != len(line):
                        print("Number of values in line {0} is different than number of announced columns in sample \"{1}\"".format(nLine, filePath))
                        continue

                    # Remove unwanted spaces
                    line = [field.replace(" ","") if field != line[0] else field for field in line]

                    # Both units have different aproaches
                    if unitInfo["unitID"] == "CAMPAIGNMANAGE":
                        # Get measurement datetime in order to ignore last 2 hours of data
                        measDateTime = datetime.strptime(line[1], unitInfo["format"])

                        if measDateTime in processEventDatetimes:
                            # Create a document by creating a dict between the header and the line and process STARTTIME
                            document = dict(zip(header, line))
                            document["STARTTIME"] = measDateTime
                            updateMongo = True

                    elif unitInfo["unitID"] == "GACTASKSTATUSLOG":
                        # Create a document by creating a dict between the header and the line and process STARTTIME
                        document = dict(zip(header,line))
                        document["STARTTIME"] = str(datetime.strptime(document["STARTTIME"].replace(" ",""), unitInfo["format"]))

                        # Parse ARCHIVE_DATE if unit ID is GACTASKSTATUSLOG
                        if "ARCHIVE_DATE" in document:
                            document["ARCHIVE_DATE"] = str(datetime.strptime(document["ARCHIVE_DATE"].replace(" ",""), unitInfo["format2"]))

                    # Process document if it is not empty
                    if document != dict():
                        # Set document granularity field and NE name
                        document["INTERVAL"] = granularity
                        document["WAD"] = ne

                        # Add current measurement time to Mongo Collection
                        if updateMongo:
                            q = {
                                "ip": self._ip_omc,
                                "collector": self._collector,
                                "fileName": fileName[1:],
                                "eventDate": str(datetime.strftime(document["STARTTIME"], "%Y-%m-%d")),
                                "eventTime": str(datetime.strftime(document["STARTTIME"], "%H:%M:%S")),
                            }
                            s = {
                                "ip": self._ip_omc,
                                "collector": self._collector,
                                "fileName": fileName[1:],
                                "eventDate": str(datetime.strftime(document["STARTTIME"], "%Y-%m-%d")),
                                "eventTime": str(datetime.strftime(document["STARTTIME"], "%H:%M:%S")),
                            }
                            query = {"query": q, "set": s}
                            self._mongoConnection.executeQuery(query, "upSert")

                        # Parse envelope data time
                        try:
                            datatime = familyObj.parseEnvelopeDataTime(str(document["STARTTIME"]))
                        except ValueError as e:
                            logger.warning("Could not build mediationEnvelope due to {0}: ".format(e), __file__)
                            continue

                        # Format document STARTTIME
                        document["STARTTIME"] = str(document["STARTTIME"])

                        # Proceed with envelope
                        familyObj.addDocument({"dataTime": datatime, "granularitySec": int(granularity * 60), "data": document})
                        self.nextOp(familyObj=familyObj, baseObject=baseObject)
                        familyObj.clearDocuments()

                    # Reset document variable in order to produce another event
                    document = dict()

            except Exception as e:
                logger.warning("Unable to process {0} due to {1}: ".format(familyObj.fileName, e), __file__)

            # Remove gunzipped file from filesystem
            if removeFile:
                os.remove(filePath)