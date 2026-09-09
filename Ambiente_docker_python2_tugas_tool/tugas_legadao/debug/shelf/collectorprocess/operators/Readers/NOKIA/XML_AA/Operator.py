#!/usr/bin/env python

__version__ = '1.0'

__doc__ = '''
Example file:
'''

__authors__ = [
				"Version 1.0: rafael-g-gomes <rafael-g-gomes@alticelabs.com>"
			]

import os
import re
import importlib
import xml.etree.cElementTree as etree
import time
from datetime import datetime
from subprocess import call

# Local libraries
BaseOperator = importlib.import_module("shelf.collectorprocess.operators.BaseOperator").BaseOperator
FamilyObject = importlib.import_module("shelf.collectorprocess.operators.FamilyObject").FamilyObject
logger = importlib.import_module("shelf.collectorprocess.logger").logger


# Command class that extends the base command defined in Operator.py
class Operator(BaseOperator):

	def __init__(self, operationParams, baseObject={}):
		BaseOperator.__init__(self, operationParams, baseObject=baseObject)
		self._file_name_regex = re.compile(r'^act.*-.*.xml$')

	def convertDateTime(self, dt, oldformat):
		try:
			dt = datetime.strptime(dt, oldformat)
		except:
			logger.warning("Invalid datetime format")
		return datetime.strftime(dt, '%Y-%m-%d %H:%M:%S')

	@property
	def line_format(self):
		return self._line_format

	def process(self, familyObj=FamilyObject(), baseObject={}):

		# Get the files to parse
		files_to_process = familyObj.getFiles()

		logger.debug("Entering XML files parser manager")

		for file_path in files_to_process:

			fileName = os.path.basename(file_path)
			logger.debug("Parsing ACT XML STATS format, in file {0}".format(fileName))
			familyObj.fileName = fileName

			try:
				#Open file for writing
				if os.path.splitext(file_path)[1] == ".gz":
					removeFile = True
					#Create a hidden, temporary file name without the .gz extension
					fileDir = os.path.dirname(file_path)
					tmp = "."  + os.path.basename(file_path)
					tmp = os.path.splitext(tmp)[0]
					filePath = os.path.join(fileDir, tmp)

					fOut = open(filePath, "w")
					call(["gunzip", "-c", file_path], stdout=fOut)

					fOut.close()

					if os.path.exists(filePath)==True:
						if os.path.getsize(filePath) == 0:
							os.remove(filePath)
							raise IOError("")
					else:
						logger.warning("Could not create a hidden file \"{}\" in read mode: ".format(file_path))
						continue
			except IOError:
				logger.warning("Could not open sample file \"{}\" in read mode: ".format(file_path), __file__)
				continue

			familyObj.clearDocuments()


			try:
				regex_fileName = re.search("^(.*)#(act.*)-([0-9]*)-([0-9]*).xml.*$", fileName)
				aaIsaId = regex_fileName.group(2)
				data = regex_fileName.group(3)
				time = regex_fileName.group(4)
				dt = data+time
				cmg = regex_fileName.group(1)

				dt = self.convertDateTime(dt, '%Y%m%d%H%M%S')
				context = iter(etree.iterparse(filePath, events=('start', 'end')))
				# get root element
				_, root = next(context)

				tag = ['time', 'aaProt', 'aaAPP', 'aaGroup', 'aaPart', 'data']

				if isinstance(tag, list):
					multi = True
				else:
					multi = False

				namespace = None
				for event, elem in context:
					if event == 'start' and namespace is None:
						if "}" in elem.tag:
							namespace = elem.tag.split("}")[0].strip("{")
							namespace = "{" + namespace + "}"
						else:
							namespace = ""

					if multi:
						if event == 'start':
							if elem.tag == namespace + 'time':
								timeT = elem.get('t')
								startTime = dt #time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(timeT)))
								elem.clear()

							elif elem.tag == namespace + 'aaProt':
								aaStatsType='aaProt'
								unitID='AAPROT'
								aaGroup = ''
								aaPart = ''

							elif elem.tag == namespace + 'aaApp':
								aaStatsType='aaAPP'
								unitID='AAAPP'
								aaGroup = ''
								aaPart = ''

							elif elem.tag == namespace + 'aaGroup':
								aaGroup = elem.get('name')

							elif elem.tag == namespace + 'aaPart':
								aaPart = elem.get('name')


							elif elem.tag == namespace + 'data':
								document = dict()
								document['AAISAID'] = aaIsaId
								document['AASTATSTYPE'] = aaStatsType
								document['AAGROUPID'] = aaGroup
								document['AAPARTITIONID'] = aaPart
								document['CMG'] = cmg
								document['T'] = timeT
								document['STARTTIME'] = startTime
								document['INTERVAL'] = 15
								for attr in elem.attrib.keys():
									if attr.upper()== 'SFC' or attr.upper()== 'NFC':
										document[attr.upper()] = elem.get(attr).replace('0x','')
									else:
										document[attr.upper()] = elem.get(attr)


									# Prepare the document for NAMF consumption
									try:
										data_time = FamilyObject.parseEnvelopeDataTime(document["STARTTIME"])
										# no granularity period available, just create one
										granularity_sec = "60"
									except ValueError as e:
										logger.error(
											"Could not build mediationEnvelope due to {0}: ".format(e), __file__)
										continue
									except KeyError as e:
										logger.error(
											"Could not build mediationEnvelope due to {0}: ".format(e), __file__)

								newdocument= {"dataTime": data_time, "granularitySec": granularity_sec, "data": document}
								familyObj.setUnitID(unitID)
								familyObj.addDocument(newdocument)
								self.nextOp(familyObj=familyObj, baseObject=baseObject)
								familyObj.clearDocuments()

						elif event == 'end':
							elem.clear()
					else:
						elem.clear()
				del context

			except IOError:
				logger.error("ERROR[{1}: Could not open sample file {0} in read mode.".format(fileName, self._command_name))

			if removeFile:
				os.remove(filePath)
