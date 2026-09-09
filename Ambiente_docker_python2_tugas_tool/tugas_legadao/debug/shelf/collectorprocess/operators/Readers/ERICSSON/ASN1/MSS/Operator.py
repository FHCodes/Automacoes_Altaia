#!/usr/bin/env python

__doc__ = \
'''
	ERICSSON ANSI MSS reader
'''

__version__ = '0.1'

__authors__ = [
				"Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>"
			]

from datetime import datetime, timedelta
import xml.etree.cElementTree as etree
from subprocess import call
import os
import re
import importlib

# Local libraries
BaseOperator = importlib.import_module("shelf.collectorprocess.operators.BaseOperator").BaseOperator
FamilyObject = importlib.import_module("shelf.collectorprocess.operators.FamilyObject").FamilyObject
logger = importlib.import_module("shelf.collectorprocess.logger").logger

class Operator(BaseOperator):

	#Class Constructor
	def __init__(self, operationParams, baseObject={}):
		BaseOperator.__init__(self, operationParams, baseObject=baseObject)

	def decodeBERWithNewPath(self, filePath, fileName):

		newFilePath = os.path.dirname(filePath) + '/.tmp_' + fileName + ".xml"

		try:
			fOut = open(newFilePath, "w")
			call(["/usr/local/bin/unber", "-p", filePath], stdout=fOut )
			#call(["/usr/local/bin/unber", filePath], stdout=fOut )
			fOut.close()
		except Exception, e:
			logger.warning(str(e) + ". Check if the 'unber' command is installed.")
			return None

		return newFilePath

	def getelements(self,filename_or_file, tag):
		context = iter(ET.iterparse(filename_or_file, events=('start', 'end')))
		_, root = next(context) # get root element
		for event, elem in context:
			if event == 'end' and elem.tag == tag:
				yield elem
				root.clear() # preserve memory

	def fixSpecialFileSpecialCharacters(self,filePath):
		try:
			#Apply sed to convert all values to readable xml values
			#call( [ "sed", "-i", "s/;&#x//g;s/>&#/>0/g;s/;</</g", filePath] )
			call([ "sed", "-i", "s/\(&#x\|;\)//g  ;  s/^<C/<root/g  ;  s/^<\/C/<\/root/g  ;  s/\( O\| T\| TL\| V\| A\| L\)=\"[^\"]*\"//g", filePath ])
		except Exception, e:
			return None
		return True

	def getTextValue(self,val):
		if val == None:
			return ""
		else:
			charList = re.findall(r"..", val)

		return "".join([x.decode("hex") for x in charList])

	def convertTimeZone(self, date):
		if '-' in date:
			d1 = datetime.strptime(date[:-5], '%Y%m%d%H%M')
			d2 = datetime.strptime('0001-01-01 ' + date[-4:-2] + ':00:00', '%Y-%m-%d %H:%M:%S')
			t1 = datetime.strptime('0001-01-01 00:00:00', '%Y-%m-%d %H:%M:%S')
			return datetime.strftime(t1 + (d1 - d2), '%Y-%m-%d %H:%M:%S')
		return datetime.strftime(datetime.strptime(date, '%Y%m%d%H%M%S'), '%Y-%m-%d %H:%M:%S')

	def strToDate(self,s):
		if 'Z' in s:
			s = s.replace('Z','')

		utc = 0
		op = ''
		if '-' in s:
			utc = int(s.split('-')[1][0:2])
		elif '+' in s:
			utc = int(s.split('+')[1][0:2])

		s = s[:14]

		timeStruct = datetime.strptime(s, "%Y%m%d%H%M%S")
		timeString = datetime.strftime("%Y-%m-%d %H:%M:%S", timeStruct)

		return timeString

	def process(self, familyObj=FamilyObject(), baseObject={}):

		filesToProcess = familyObj.getFiles()
		familyObj.clearFiles()

		logger.debug("[Reader] Reading ERICSSON Performance ANSI files' contents...")

		line_padding = False
		if 'line_padding' in self.options.keys():
			if self.options['line_padding'] == 'True':
				line_padding = True

		for filePath in filesToProcess:
			familyObj_dict=dict()
			#Get file's name to find the unitID
			fileName = os.path.basename(filePath)
			familyObj.fileName = fileName

			try:
				if os.path.getsize(filePath) == 0:
					logger.warning("The File \"{0}\" has 0 bytes".format(fileName))
					continue
			except Exception, e:
				logger.warning("No such file or directory '{0}' in sample file \"{0}\"".format(e, fileName))
				continue

			# Unber File
			newFilePath = self.decodeBERWithNewPath(filePath, fileName)
			if not newFilePath:
				logger.warning("Could not decode sample \"{0}\"".format(filePath))
				continue
			else:
				filePath = newFilePath

			# Convert and corrects special charaters
			if not self.fixSpecialFileSpecialCharacters(filePath):
				logger.warning("Unable to call 'sed' command for file \"{0}\"".format(os.path.basename(filePath)))
				continue

			try:
				self.fast_iter(filePath, familyObj, baseObject, line_padding)
			except Exception, e:
				logger.warning("" + str(e) + " in file \"{0}\"".format(fileName))

			#Delete the temporary file
			try:
				os.remove(filePath)
			except Exception, e:
				logger.warning("Could not remove file after processing \"{0}\"".format(fileName))


	def fast_iter(self, filePath, familyObj, baseObject, line_padding):
		context = iter(etree.iterparse(filePath, events=('start', 'end')))
		# get root element
		_, root = next(context)

		tag = ['C', 'I', 'P']

		if isinstance(tag, list):
			multi = True
		else:
			multi = False

		newDocument = dict()
		familyHeaderData = dict()
		nEUserName = ''
		level = ['root']
		headerReaded = False
		headerData = dict()
		headerField = ['FILEFORMATVERSION', 'SENDERNAME', '', 'VENDORNAME', 'MEASSTARTTIME']
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
					dataValue = ''
					if elem.tag == namespace + 'C' or elem.tag == namespace + 'I':
						if level[-1] == 'root':
							valueErrorEncounter = False
							if not headerReaded:
								level.append('header')
							elif 'dataBlock' not in level:
								level.append('dataBlock')

						elif level[-1] == 'dataBlock':
							if 'dataSequence' not in level:
								level.append('dataSequence')

						elif level[-1] == 'dataSequence':
							if nEUserName == '':
								level.append('nEUserName')
							else:
								level.append('nEInfoBlock')

						elif level[-1] == 'nEInfoBlock':
							level.append('familyHeader')
							familyHeaderList = ['MEASENDTIME', 'GRANULARITYPERIOD']
							counters = False

						elif level[-1] == 'familyHeader':
							if not counters:
								countersList = list()
								level.append('familyCounters')
							else:
								level.append('familyValuesUpper')
						elif level[-1] == 'familyValuesUpper':
							level.append('familyMeasuredObjectID')
							countersListTmp = countersList[:]
						elif level[-1] == 'familyMeasuredObjectID':
							level.append('familyValues')

					elif elem.tag == namespace + 'P':
						try:
							dataValue = elem.text
						except Exception as e:
							logger.warning(e)
							return

					elem.clear()

				elif event == 'end':
					if elem.tag == namespace + 'C' or elem.tag == namespace + 'I':
						if level[-1] == 'header':
							headerReaded = True
						elif level[-1] == 'dataSequence':
							nEUserName = ''
						elif level[-1] == 'familyCounters':
							counters = True
						elif level[-1] == 'familyHeader':
							familyHeaderList = ['MEASENDTIME', 'GRANULARITYPERIOD']
						elif level[-1] == 'familyMeasuredObjectID':
							if valueErrorEncounter:
								if line_padding:
									logger.warning("Number of measurement types is differente than number of result values in measUnit {0} in sample \"{1}\", but was processed.".format(newDocument['MEASUREDOBJECTID'].upper().split('.')[0], fileName))
								else:
									logger.warning("Number of measurement types is differente than number of result values in measUnit {0} in sample \"{1}\"".format(newDocument['MEASUREDOBJECTID'].upper().split('.')[0], fileName))

							if (line_padding or not valueErrorEncounter) and 'MEASUREDOBJECTID' in newDocument.keys():
								newDocument['NEUSERNAME'] = nEUserName

								for attr in headerData.keys():
									if attr not in ['', '00', None]:
										newDocument[attr] = headerData[attr]
								for attr in familyHeaderData.keys():
									if attr not in ['', '00', None]:
										newDocument[attr] = familyHeaderData[attr]

								try:
									data_time = familyObj.parseEnvelopeDataTime(newDocument["MEASSTARTTIME"])
									granularity_sec = familyObj.parseEnvelopeGranularitySec(newDocument["GRANULARITYPERIOD"])
								except ValueError as e:
									logger.warning("Could not build mediationEnvelope due to {0}: ".format(e), __file__)
									continue

								familyObj.clearDocuments()
								familyObj.setUnitID(newDocument['MEASUREDOBJECTID'].upper().split('.')[0])

								data_document = {"dataTime": data_time, "granularitySec": granularity_sec, "data": newDocument}
								familyObj.addDocument(data_document)
								self.nextOp(familyObj = familyObj, baseObject = baseObject)
								newDocument = dict()

						if level[-1] != 'root':
							level.remove(level[-1])

					elif elem.tag == namespace + 'P':

						if dataValue in ['', None]:
							try:
								if elem.text not in ['', None]:
									dataValue = elem.text
								else:
									dataValue = ''
							except:
								pass

						if level[-1] == 'header':
							try:
								if headerField[0] == 'FILEFORMATVERSION':
									try:
										headerData[headerField[0]] = int(dataValue, 16)
									except:
										headerData[headerField[0]] = self.getTextValue(dataValue)

								elif headerField[0] == 'MEASSTARTTIME':
									headerData[headerField[0]] = self.convertTimeZone(self.getTextValue(dataValue))
								else:
									headerData[headerField[0]] = self.getTextValue(dataValue)
								headerField.remove(headerField[0])
							except Exception as e:
								print e
								continue


						elif level[-1] == 'nEUserName':
							if nEUserName == '':
								nEUserName = self.getTextValue(dataValue)


						elif level[-1] == 'familyHeader':
							try:
								if dataValue not in ['', '00', None]:
									if familyHeaderList[0] == 'GRANULARITYPERIOD':
										try:
											familyHeaderData[familyHeaderList[0]] = str(int(dataValue, 16))
										except Exception as ex:
											pass
									else:
										familyHeaderData[familyHeaderList[0]] = self.convertTimeZone(self.getTextValue(dataValue))
									familyHeaderList.remove(familyHeaderList[0])
							except:
								pass


						elif level[-1] == 'familyCounters':
							countersList.append(self.getTextValue(dataValue))

						elif level[-1] == 'familyValues':

							if countersListTmp != []:
								if countersListTmp[0] not in ['', '00', None]:
									try:
										newDocument[countersListTmp[0]] = str(int(dataValue, 16))
									except:
										newDocument[countersListTmp[0]] = self.getTextValue(dataValue)
								countersListTmp.remove(countersListTmp[0])
							else:
								valueErrorEncounter = True

						elif level[-1] == 'familyMeasuredObjectID':
							if 'MEASUREDOBJECTID' not in newDocument.keys() and dataValue not in ['', None]:
								newDocument['MEASUREDOBJECTID'] = self.getTextValue(dataValue)

					elem.clear()
			else:
				elem.clear()
		del context
