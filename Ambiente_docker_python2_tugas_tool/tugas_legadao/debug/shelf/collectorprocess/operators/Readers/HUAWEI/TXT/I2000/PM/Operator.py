#!/usr/bin/env python

__doc__ = \
	'''
	Huawei I2000 Performance CSV reader
'''

__version__ = '0.1'

__authors__ = [
	"Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>"
]

from datetime import datetime, timedelta
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

	def formatData(self, document):
		hours = document['HORA'][:2]
		minutes = (document['HORA'][-2:] if len(document['HORA']) >= 4 else '00')
		if re.match(r'[0-9]{2}/[0-9]{2}/[0-9]{4}', document['DATA']):
			return datetime.strftime(datetime.strptime('{:s} {:s}:{:s}:00'.format(document['DATA'], hours, minutes), '%d/%m/%Y %H:%M:%S'), '%Y-%m-%d %H:%M:%S')
		elif re.match(r'[0-9]{8}', document['DATA']):
			return datetime.strftime(datetime.strptime('{:s} {:s}:{:s}:00'.format(document['DATA'], hours, minutes), '%Y%m%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S')

	def process(self, familyObj=FamilyObject(), baseObject={}):

		filesToBeProcessed = familyObj.getFiles()
		familyObj.clearFiles()

		line_padding = False
		if 'line_padding' in self.options.keys():
			if self.options['line_padding'] == 'True':
				line_padding = True

		for originalFilePath in filesToBeProcessed:

			fileName = os.path.basename(originalFilePath)
			familyObj.fileName = fileName

			familyObj.setUnitID(re.match(r'^(?P<unitID>.*?)_\d*.txt.*$', fileName).group('unitID').upper())

			logger.debug("Parsing Huawei TXT OCS I2000 format, in file {0}".format(fileName))
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
				try:
					#Open file for reading
					f = open(filePath, 'r')
				except IOError:
					logger.warning("Could not open sample file \"{}\" in read mode: ".format(fileName))

				# Used to store the column names from the first line of each file
				column_names_list = None
				n_column_names = 0
				n_line = 0

				for line in reader(f,delimiter=';'):
					if not line or line == '':
						continue

					n_line += 1

					# Collects column names from first line of file
					if n_line == 1:
						if len(line) == 0:
							logger.warning(
								"No column names found in first line of file \"{0}\"".format(fileName), __file__)
							break

						column_names_list = [x.upper() for x in line]
						n_column_names = len(column_names_list)
						continue


					# Checks if number of values in row is the same as the announced columns in the first line
					if len(line) != n_column_names:
						document = dict()
						if not line_padding:
						continue

						i = 0
						for value in line:
						document[column_names_list[i]] = value
						i += 1
					else:
						document = dict(zip(column_names_list, line))

					document["RESULTTIME"] = self.formatData(document)

					try:
						try:
							data_time = familyObj.parseEnvelopeDataTime(document["RESULTTIME"])
						except ValueError as e:
							logger.warning("Could not build mediationEnvelope due to {0}: ".format(e), __file__)
							continue

						familyObj.clearDocuments()
						familyObj.addDocument({"dataTime": data_time, "granularitySec": int(document['PERIOD_DURATION']), "data": document})
						self.nextOp(familyObj=familyObj, baseObject=baseObject)
					except Exception, e:
						logger.warning("Unable to process {0} in unit {1} because wrong format => {2}".format(fileName, self._command_name, e), __file__)
						continue
			except IOError:
				logger.error("ERROR[self._command_name]: Could not open sample file {0} in read mode.".format(fileName))

			if removeFile:
				os.remove(filePath)
