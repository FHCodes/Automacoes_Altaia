#!/usr/bin/env python

__doc__ = \
	'''
	CONDOR CCM Performance CSV reader
'''

__version__ = '0.1'

__authors__ = [
	"Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>"
]


from csv import reader
import os
import re
import importlib
import json

# Local libraries
BaseOperator = importlib.import_module("shelf.collectorprocess.operators.BaseOperator").BaseOperator
FamilyObject = importlib.import_module("shelf.collectorprocess.operators.FamilyObject").FamilyObject
logger = importlib.import_module("shelf.collectorprocess.logger").logger
mongoCon = importlib.import_module("shelf.collectorprocess.operators.OutputManagers.Mongo.Operator").mongoConnection

class Operator(BaseOperator):

	# Class Constructor
	def __init__(self, operationParams, baseObject={}):
		BaseOperator.__init__(self, operationParams, baseObject=baseObject)
		self._mongoConnection = mongoCon(json.load(open('/opt/alticelabs/namf/src/shelf/collectorprocess/config/mongo_config.json')))

	def process(self, familyObj=FamilyObject(), baseObject={}):
		counters_for_family = json.load(open('/opt/alticelabs/namf/src/shelf/collectorprocess/operators/Readers/CONDOR/CSV/CCM/mappingCounterforFamily.json'))
		regex_filename = re.compile("^(?P<hostname>.+?)_(?P<day>\d{8})_(?P<hour>\d{6})")
		files_to_process = familyObj.getFiles()
		familyObj.clearDocuments()

		logger.debug("Reading CONDOR Performance CSV files' contents...", __file__)
		mongoCollection = self._mongoConnection.getConnection()

		for filePath in files_to_process:

			#Get files name to find the unitID
			fileName = os.path.basename(filePath)
			if os.path.getsize(filePath) == 0:
				logger.warning("The File \"{0}\" has 0 bytes".format(fileName))
				continue

			familyObj.clearDocuments()
			familyObj.fileName = fileName

			regexmatch=regex_filename.match(familyObj.fileName)
			if regexmatch == None:
				logger.warning("Filename not expected \"{0}\" ".format(fileName))
				continue

			#Get the unit from the filename
			hostname = regexmatch.group('hostname')
			day = regexmatch.group('day')
			nameofFile=hostname+'_'+day
			try:
				#Open file for reading
				f = open(filePath, 'r')
			except IOError:
				logger.warning("Could not open sample file \"{}\" in read mode: ".format(fileName))
				continue

			fileIp = re.search(r'(?P<IP>\d+\.\d+\.\d+\.\d+)', filePath).group('IP')
			queryResult = self._mongoConnection.executeQuery({"collector": "CONDOR_CCM_IMS_PM_CCM", "ip": fileIp, "fileName": nameofFile}, 'find_one')
			if queryResult != None:
				lineInMem = queryResult['numLine']
			else:
				lineInMem = -1

			blockLine = True

			n_line = -1
			for line in reader(f,delimiter=','):

				n_line += 1

				# block line
				if n_line-1 == lineInMem:
					blockLine = False

				if blockLine:
					continue

				#set unitID obtained in filename
				familyObj.setUnitID(line[2].upper())
				# Used to store the column names from the first line of each file
				if line[2].upper() in counters_for_family.keys():
					column_names_list = counters_for_family[line[2].upper()]
					n_column_names = len(column_names_list)
				else:
					logger.warning("Unknow unitID {0} of announced in sample \"{1}\"".format(str(line[2].upper()), fileName), __file__)
					continue

				if not line:
					continue

				if len(line) == 0:
					logger.warning("No column names found in line \"{0}\ of file \"{1}\"".format(str(n_line), fileName))
					break

				# Checks if number of values in row is the same as the announced columns in the first line
				if len(line) != n_column_names:
					logger.warning(
						"Number of values in line {0} is different than number of announced columns in sample \"{1}\"".format(str(n_line), fileName), __file__)
					# If values < header
					if len(line) < n_column_names:
						diff = n_column_names - len(line)
						line += [None] * diff

					# If len(line) > n_column_names - values > header
					else:
						line = line[:n_column_names]

				document = dict(zip(column_names_list, line))
				document["DATETIME"] = document["DATE"] + ' ' + document["TIME"]
				document["HOSTNAME"] = hostname
				document["INTERVAL"] = 5

				try:
					try:
						data_time = familyObj.parseEnvelopeDataTime(document["DATETIME"])
						granularity_sec = familyObj.parseEnvelopeGranularitySec(int(document["INTERVAL"]))
					except ValueError as e:
						logger.warning("Could not build mediationEnvelope due to {0}: ".format(e), __file__)
						continue

					familyObj.addDocument({"dataTime": data_time, "granularitySec": granularity_sec, "data": document})

					# Final operations to the fields with timestamp and granularity period

					self.nextOp(familyObj=familyObj, baseObject=baseObject)
					familyObj.clearDocuments()

				except Exception, e:
					logger.warning("Unable to process {0} in unit {1} because wrong format => {2}".format(familyObj.fileName, familyObj.unitID, e), __file__)
					continue

			# update or insert
			if queryResult == None:
				self._mongoConnection.executeQuery({"collector": "CONDOR_CCM_IMS_PM_CCM", "ip": fileIp, "fileName": nameofFile, "numLine": n_line, "date": day, "hour": regexmatch.group('hour')}, 'insert')
			else:
				self._mongoConnection.executeQuery({"query":{"collector": "CONDOR_CCM_IMS_PM_CCM", "ip": fileIp, "fileName": nameofFile, "date": day}, "set": {"numLine": n_line, "hour": regexmatch.group('hour')}}, 'update')