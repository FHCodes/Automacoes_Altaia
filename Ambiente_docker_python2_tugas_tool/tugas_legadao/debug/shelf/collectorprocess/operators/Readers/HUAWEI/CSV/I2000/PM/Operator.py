#!/usr/bin/env python

__doc__ = \
	'''
	Huawei I2000 Performance CSV reader
'''

__version__ = '0.1'

__authors__ = [
	"Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>"
]


from csv import reader
import os
import re
import gzip
import io
from subprocess import call
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

		files_to_process = familyObj.getFiles()
		regex_date='\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}'

		logger.debug("Reading Huawei I2000 Performance CSV files' contents...", __file__)
		for filePath in files_to_process:
			originalFilePath = filePath
			familyObj.clearDocuments()

			# Get file's name to find the unitID
			fileName = os.path.basename(filePath)
			familyObj.fileName = fileName

			try:
				#Open file for writing
				if os.path.splitext(originalFilePath)[1] == ".gz":
					removeFile = True
					#Create a hidden, temporary file name without the .gz extension
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

			try:
				# Open file for writing
				f = open(filePath, 'r')
			except IOError:
				logger.error("Could not open sample file \"{0}\" in read mode: ".format(fileName), __file__)
				continue

			# Used to store the column names from the first line of each file
			columnNamesList = None
			nColumnNames = 0
			n_line = 0

			for line in reader(f):
				try:
					familyObj.clearDocuments()

					n_line += 1

					# Collects column names from first line of file
					if n_line == 1:
						if len(line) == 0:
							logger.warning(
								"No column names found in first line of file \"{0}\"".format(fileName), __file__)
							break
						columnNamesList = [x.upper() for x in line]
						nColumnNames = len(columnNamesList)
						continue

					# Checks if number of values in row is the same as the announced columns in the first line
					if len(line) != nColumnNames:
						logger.warning(
							"Number of values in line {0} is different than number of announced columns in sample \"{1}\"".format(n_line, fileName), __file__)
						continue

					document = dict(zip(columnNamesList, line))
					try:
						# Result time comes with the format YYYY-MM-DD HH:mm The preferred format is YYYY-MM-DD HH:mm:ss
						regexmatch=re.match(regex_date, document["COLLECTIONBEGINTIME"])
						document["COLLECTIONBEGINTIME"]=regexmatch.group()

						familyObj.setUnitID(document["MU"])

						try:
							data_time = familyObj.parseEnvelopeDataTime(document["COLLECTIONBEGINTIME"])
							granularity_sec = familyObj.parseEnvelopeGranularitySec(int(document["GRANULARITY"]))
						except ValueError as e:
							logger.warning("Could not build mediationEnvelope due to {0}: ".format(e), __file__)
							continue

						familyObj.addDocument({"dataTime": data_time, "granularitySec": granularity_sec, "data": document})

						# Final operations to the fields with timestamp and granularity period
						self.nextOp(familyObj=familyObj, baseObject=baseObject)

					except Exception, e:
						logger.warning("Unable to process {0} in unit {1} because wrong format => {2}".format(familyObj.fileName, unit_id, e), __file__)
						continue
				except Exception as e:
					logger.warning("Unable to process {0} because wrong format => {1}".format(familyObj.fileName, e), __file__)
			if removeFile:
				os.remove(filePath)
