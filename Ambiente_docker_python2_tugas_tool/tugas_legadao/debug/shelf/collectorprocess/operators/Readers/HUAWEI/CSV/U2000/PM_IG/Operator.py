#!/usr/bin/env python

__doc__ = \
	'''
	Huawei U2000 Performance CSV reader
'''

__version__ = '1.2'

__authors__ = [
	"Version 0.1: Francisco Santiago <francisco-j-santiago@telecom.pt>"
	"Version 1.1: Joao Pio <joao-t-pio@telecom.pt>"
	"Version 1.2: Bruno Silva <bruno-e-silva@alticelabs.com>"
]


from csv import reader
import csv
import os
import re
from datetime import datetime
import importlib

# Local libraries
BaseOperator = importlib.import_module("shelf.collectorprocess.operators.BaseOperator").BaseOperator
FamilyObject = importlib.import_module("shelf.collectorprocess.operators.FamilyObject").FamilyObject
logger = importlib.import_module("shelf.collectorprocess.logger").logger


class Operator(BaseOperator):

	# Class Constructor
	def __init__(self, operationParams, baseObject={}):
		BaseOperator.__init__(self, operationParams, baseObject=baseObject)

	def process(self, familyObj=FamilyObject(), baseObject={}):

		filesToProcess = familyObj.getFiles()
		familyObj.clearDocuments()

		logger.debug("[Reader] Reading Huawei Performance IG CSV files' contents...")

		for filePath in filesToProcess:

			#Get file's name to find the unitID
			fileName = os.path.basename(filePath)

			familyObj = FamilyObject()
			familyObj.fileName = fileName
			try:
				familyObj.unitID = re.match(r".*?PM_IG(?P<unitID>\d+)_.*?", fileName).group("unitID")
			except Exception as e:
				logger.warning(e)
				logger.warning("Could not extract unit ID of name in sample file \"{}\"  ".format(fileName))
				continue
			try:
				#Open file for writing
				f = open(filePath, 'r')
			except IOError:
				logger.warning("Could not open sample file \"{}\" in read mode: ".format(fileName))
				continue

			#Used to store the column names from the first line of each file
			columnNamesList = None
			nColumnNames = 0

			nLine = 0
			try:
				for line in reader(f):
					nLine += 1

					if nLine == 1:
						continue

					#Collects column names from first line of file
					if nLine == 2:
						if len(line) == 0:
							logger.warning("No column names found in first line of file \"{0}\"".format(fileName))
							break

						columnNamesList = [ x.upper() for x in line ]
						nColumnNames = len(columnNamesList)
						continue

					#Checks if number of values in row is the same as the announced columns in the first line
					if len(line) != nColumnNames:
						logger.warning("Number of values in line {0} is different than number of announced columns in sample \"{1}\"".format(nLine, fileName))
						continue

					document = dict(zip(columnNamesList, line))
					try:
						try:
							# Result time comes with the format YYYY-MM-DD HH:mm The preferred format is YYYY-MM-DD HH:mm:ss
							document["COLLECTIONTIME"] += ":00"

						except Exception, e:
							logger.warning("Could not convert COLLECTIONTIME due to '{0}'".format(e), __file__)

						try:
							# Handle multiple file formats
							try:
								document["COLLECTIONTIME"] = datetime.strftime(datetime.strptime(document["COLLECTIONTIME"], "%m/%d/%Y %H:%M:%S"), "%Y-%m-%d %H:%M:%S")
								data_time = familyObj.parseEnvelopeDataTime(document["COLLECTIONTIME"])
							except:
								document["COLLECTIONTIME"] = datetime.strftime(datetime.strptime(document["COLLECTIONTIME"][:-3], "%Y-%m-%d %H:%M:%S"), "%Y-%m-%d %H:%M:%S")
								data_time = familyObj.parseEnvelopeDataTime(document["COLLECTIONTIME"])

						except ValueError as e:
							logger.warning("Could not build mediationEnvelope due to {0}: ".format(e), __file__)
							continue



						familyObj.addDocument({"dataTime": data_time, "granularitySec": int(document["GRANULARITYPERIOD"]), "data": document})

						# Final operations to the fields with timestamp and granularity period

						self.nextOp(familyObj=familyObj, baseObject=baseObject)
						familyObj.clearDocuments()

					except Exception, e:
						logger.warning("Unable to process {0} in unit {1} because wrong format => {2}".format(familyObj.fileName, familyObj.unitID, e), __file__)
						continue

			except csv.Error, e:
				logger.warning("{0} in file '{1}'.".format(e, fileName))
