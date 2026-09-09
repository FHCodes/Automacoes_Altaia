#!/usr/bin/env python

__doc__ = \
'''
	Enrichment Operator
'''

__version__ = '0.1'

__authors__ = [
				"Version 0.1: Francisco Santiago <francisco-j-santiago@telecom.pt>"
			]

#import vendorConvert
import gzip
from csv import reader
import csv
import importlib
import os
import re

import unicodedata

# Local libraries
BaseOperator = importlib.import_module("shelf.collectorprocess.operators.BaseOperator").BaseOperator
FamilyObject = importlib.import_module("shelf.collectorprocess.operators.FamilyObject").FamilyObject
logger = importlib.import_module("shelf.collectorprocess.logger").logger

def strip_accents(s):
		s = unicode(s, 'Cp1252')
		return ''.join(c for c in unicodedata.normalize('NFD', s)
			if unicodedata.category(c) != 'Mn')

class Operator(BaseOperator):

	#Class Constructor
	def __init__(self, operationParams, baseObject={}):
		BaseOperator.__init__(self, operationParams, baseObject=baseObject)

		self._polls = dict()
		self._lastReportedTimestamp = ""



	def process(self, familyObj=FamilyObject(), baseObject={}):

		for filePath in familyObj.files:

			#Get file's name
			familyObj.fileName = os.path.basename(filePath)

			try:
				#Open file for writing
				#f = open(filePath, 'r')
				f=gzip.open(filePath)
			except IOError:
				logger.warning("Could not open sample file '{}' in read mode: ".format(familyObj.fileName))
				continue

			familyObj.unitID = re.sub(r"cadastro_tdt_(\w+)\.txt.gz", r"\1", familyObj.fileName).upper()

			columnNames = None
			nColumnNames = None

			nLine = 0
			try:

				for line in reader(f, delimiter=";"):

					line = [item.decode("latin-1") for item in line]

					nLine += 1

					if nLine == 1:

						nColumnNames = len(line)
						#Fix name of first element of row that has a # character attached
						if nColumnNames > 0:
							line[0] = line[0].strip("#")

							#Store column names into a list
							columnNames = [ name.upper() for name in line ]
						else:
							logger.warning("Could not retrieve column names from first row of sample '{1}'".format(familyObj.fileName))
							break

					else:
						if len(line) == nColumnNames:

							document = dict(zip(columnNames, line))

							convertedDateTime = re.sub(r"(\d\d\d\d)(\d\d)(\d\d)", r"\1-\2-\3 00:00:00", document["DATA"])
							#document["LOCATION"] = strip_accents(document["LOCATION"])
							document["DATA"] = convertedDateTime

							try:
								data_time = familyObj.parseEnvelopeDataTime(document["DATA"])
							except ValueError as e:
								logger.warning("Could not build mediationEnvelope due to {0}: ".format(e), __file__)
								continue

							# envelope
							familyObj.addDocument({"dataTime": data_time, "granularitySec": 1440, "data": document})
							self.nextOp(familyObj=familyObj, baseObject=baseObject)
							familyObj.clearDocuments()
						else:
							logger.warning("Number of values in line {0} is different than number of announced columns in sample '{1}'".format(nLine, familyObj.fileName))



			except csv.Error, e:
				logger.warning("{0} in line {1} of file {2}".format(e, nLine, familyObj.fileName))
