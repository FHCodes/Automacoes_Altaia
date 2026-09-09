#!/usr/bin/env python

__doc__ = \
	'''
	NEC PTN Performance TXT reader
'''

__version__ = '1.2'

__authors__ = [
	"Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>"
]


from csv import reader
import os
import re
import importlib
import json
import zipfile
from datetime import datetime

# Local libraries
BaseOperator = importlib.import_module("shelf.collectorprocess.operators.BaseOperator").BaseOperator
FamilyObject = importlib.import_module("shelf.collectorprocess.operators.FamilyObject").FamilyObject
logger = importlib.import_module("shelf.collectorprocess.logger").logger


class Operator(BaseOperator):

	# Class Constructor
	def __init__(self, operationParams, baseObject={}):
		BaseOperator.__init__(self, operationParams, baseObject=baseObject)

	def process(self, familyObj=FamilyObject(), baseObject={}):

		files_to_process = familyObj.getFiles()
		familyObj.clearFiles()

		logger.debug("Reading NEC PTN Performance TXT files' contents...", __file__)
		for filePath in files_to_process:
			data = {}
			unitID='GENERIC'

			#Get file's name to find the unitID
			fileName = os.path.basename(filePath)

			if os.path.getsize(filePath) == 0:
				logger.warning("The File \"{0}\" has 0 bytes".format(fileName))
				continue

			try:
				regex_fileName=re.search("^e([0-9]+)#A(.*?)_(.*?).zip$", fileName)
				equipmentId=regex_fileName.group(1)
				granularity=regex_fileName.group(2)
				dt=regex_fileName.group(3)

				file_zip = zipfile.ZipFile(filePath)
				file = 'A' + granularity + '_'+ dt + '.per'
			except:
				logger.warning("The File \"{0}\" has a different name was expected".format(fileName))
				continue

			if equipmentId == None:
				equipmentId = ''
				logger.warning("Could not find EQUIPMENT ID (PTN) for File \"{0}\" ".format(fileName))

			if granularity == None:
				granularity = ''
				logger.warning("The File Name: \"{0}\" is not valid granularity value".format(fileName))

			if dt == None:
				dt=''
				logger.warning("The File Name: \"{0}\" is a invalid format of date ".format(fileName))

			# Garantir que so tratamos os ficheiros de granularidade 15
			if granularity == '15':
				try:
					dt = datetime.strptime(dt, '%Y%m%d%H%M')
					dt = datetime.strftime(dt, "%Y-%m-%d %H:%M:%S")
				except:
					dt = ''
					logger.warning("The File Name: \"{0}\" is not valid".format(fileName))

				with file_zip.open(file) as f:
					document = dict()
					first = True
					#found = False
					i = 0
					interfacetype = ''
					linesData = f.readlines()
					for line in linesData:
						line = line.strip()
						if line != '':
							line = re.split(r'[=\s]+', line)[1:]
							#print line
							if i == 0 :
								interfacetype = line[0]
							else:
								counter = line[0].upper()
								if "\\\\\\" in counter:
									if document != dict():
										familyObj.clearDocuments()
										familyObj.setUnitID(unitID)
										try:
											try:
												data_time = familyObj.parseEnvelopeDataTime(document["DATETIME"])
												granularity_sec = familyObj.parseEnvelopeGranularitySec(int(document["GRANULARITYPERIOD"]))
											except ValueError as e:
												logger.warning("Could not build mediationEnvelope due to {0}: ".format(e), __file__)
												continue

											familyObj.addDocument({"dataTime": data_time, "granularitySec": granularity_sec, "data": document})

											# Final operations to the fields with timestamp and granularity period

											self.nextOp(familyObj=familyObj, baseObject=baseObject)
										except Exception, e:
											logger.warning("Unable to process {0} in unit {1} because wrong format => {2}".format(familyObj.fileName, unitID, e), __file__)
											continue
									document = dict()
									document['SERVICEID'] = line[1]
									document['INTERFACETYPE'] = interfacetype
									document['DATETIME'] = dt
									document['GRANULARITYPERIOD'] = granularity
									document['PTN'] = equipmentId
								else:
									document[counter] = line[1]
						i += 1

						if i >= len(linesData):
							familyObj.clearDocuments()
							familyObj.setUnitID(unitID)
							try:
								try:
									data_time = familyObj.parseEnvelopeDataTime(document["DATETIME"])
									granularity_sec = familyObj.parseEnvelopeGranularitySec(int(document["GRANULARITYPERIOD"]))
								except ValueError as e:
									logger.warning("Could not build mediationEnvelope due to {0}: ".format(e), __file__)
									continue

								familyObj.addDocument({"dataTime": data_time, "granularitySec": granularity_sec, "data": document})

								# Final operations to the fields with timestamp and granularity period

								self.nextOp(familyObj=familyObj, baseObject=baseObject)
							except Exception, e:
								logger.warning("Unable to process {0} in unit {1} because wrong format => {2}".format(familyObj.fileName, unitID, e), __file__)
								continue

			else:
				logger.warning("It was not possible to relate counters to unit. Counters Name do not match! File: \"{0}\"".format(fileName))
