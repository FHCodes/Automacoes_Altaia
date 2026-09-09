__version__ = '1.0'

__doc__ = '''
	MEO vEPC (Embedded Packet Capture) Enrich Reader
'''

__authors__ = [
	"Version 1.0: bruno-e-silva <bruno-e-silva@alticelabs.com>"
]

import re
import os
import csv
import copy
import importlib
from datetime import datetime

# Local libraries
BaseOperator = importlib.import_module("shelf.collectorprocess.operators.BaseOperator").BaseOperator
FamilyObject = importlib.import_module("shelf.collectorprocess.operators.FamilyObject").FamilyObject
logger = importlib.import_module("shelf.collectorprocess.logger").logger

class Operator(BaseOperator):

	# Class constructor
	def __init__(self, operationParams, baseObject={}):
		BaseOperator.__init__(self, operationParams, baseObject=baseObject)

	def process(self, familyObj=FamilyObject(), baseObject={}):
		logger.debug("Reading MEO vEPC ENRICH file' contents...", __file__)
		filePath = familyObj.getFiles()[0]
		familyObj.clearDocuments()

		# If file is empty, bota fora :)
		if os.path.getsize(filePath) == 0:
			logger.warning("File {0} is empty.".format(os.path.basename(filePath)), __file__)
			return

		# Get file's name
		fileName = os.path.basename(filePath)
		familyObj.fileName = fileName

		# Set Unit ID
		familyObj.setUnitID("EPC_BSC")

		# Get datetime from filename
		fileNameRegex = re.compile(r'epc_dados_(?P<datetime>\d+)\.csv').match(fileName)

		# Parse timestamp from filename
		timestamp = datetime.strptime(fileNameRegex.group("datetime"), "%Y%m%d%H%M")
		timestamp = datetime.strftime(timestamp, "%Y-%m-%d %H:%M:%S")
		# Open the sample file in reading mode
		try:
			f = open(filePath, 'r')
		except IOError:
			logger.error("Could not open sample file \"{0}\" in read mode: ".format(fileName), __file__)

		 # Parse envelope DataTime
		try:
			data_time = familyObj.parseEnvelopeDataTime(timestamp)
		except ValueError as e:
			logger.warning("Could not build mediationEnvelope due to {0}: ".format(e), __file__)
			return

		# Try parsing the CSV file
		try:
			for line in csv.reader(f):
				document=dict()
				document["DATETIME"] = timestamp
				document["GRANULARITYPERIOD"] = 1440
				# Skip empty lines
				if not line:
					continue

				# Get EPC name
				document["EPC"] = line[0]

				# Since the CSV file has 2 columns (EPC and Info), apply a regex to the info column
				# and get NSEI and BSCNAME
				lineRegex = re.compile(r'^nsei (?P<NSEI>\d+) name (?P<BSCNAME>.+)$').match(line[1])

				# Only parse lines that matched previous regex
				if lineRegex:
					document["NSEI"] = lineRegex.group("NSEI")
					document["BSCNAME"] = lineRegex.group("BSCNAME")

					# Proceed with mediation envelope
					familyObj.addDocument({"dataTime": data_time, "granularitySec": int(document["GRANULARITYPERIOD"]*60), "data": document})
					self.nextOp(familyObj=familyObj, baseObject=baseObject)
					familyObj.clearDocuments()

		except Exception as e:
			logger.warning("Unable to process file {0} because => {1}".format(familyObj.fileName, e), __file__)
			return
