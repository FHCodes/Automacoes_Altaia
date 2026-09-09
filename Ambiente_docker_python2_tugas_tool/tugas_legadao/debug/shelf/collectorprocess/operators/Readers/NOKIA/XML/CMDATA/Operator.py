__doc__ = \
'''
	Parser for Parameters NSN using sax
	v1.1: Changed mongo writeConcern to 0 and adde mongo insert via Bulk
'''

__version__ = '1.1'

__authors__ = [
				"Version 1.0: Bruno Silva <bruno-e-silva@alticelabs.com>"
				"Version 1.1: Paulo Gil <paulo-a-gil@alticelabs.com>"
			]

import re, os, json
import copy
import HierarchyManager
import xml.etree.cElementTree as etree
import importlib

# Local libraries
BaseOperator = importlib.import_module("shelf.collectorprocess.operators.BaseOperator").BaseOperator
FamilyObject = importlib.import_module("shelf.collectorprocess.operators.FamilyObject").FamilyObject
logger = importlib.import_module("shelf.collectorprocess.logger").logger
mongoCon = importlib.import_module("shelf.collectorprocess.operators.OutputManagers.Mongo.Operator").mongoConnection


class Operator(BaseOperator):

	def __init__(self, operationParams, baseObject={}):
		BaseOperator.__init__(self, operationParams, baseObject=baseObject)
		config = json.load(open('/opt/alticelabs/namf/src/shelf/collectorprocess/config/mongo_enrich_config.json'))
		config.update(json.load(open('{0}/{1}/config.json'.format(config['location'], self.options['enrich'].replace('.','/')))))
		self._mongoConnection = mongoCon(config)
		self._mongoConnection.getConnection(0) # Passing 0 to set writeConcern to 0

	def process(self, familyObj=FamilyObject(), baseObject={}):

		logger.debug("[Reader] Reading NSN Parameters XML files' contents...")

		filesToBeProcessed = familyObj.getFiles()
		familyObj.clearFiles()

		for filePath in filesToBeProcessed:

			fileName = os.path.basename(filePath)
			familyObj.fileName = fileName

			#logger.warning(fileName +': '+ str(os.path.getsize(filePath)))
			if os.path.getsize(filePath) == 0:
				continue

			cellIDDict2G = dict()
			cellIDDict3G = dict()
			cellIDDict4G = dict()
			cellIDDict5G = dict()

			logger.warning('Starting to process file: {}'.format(fileName))
			self.enrichData(filePath, cellIDDict2G, cellIDDict3G, cellIDDict4G, cellIDDict5G)
			self.fast_iter(filePath, familyObj, baseObject, cellIDDict2G, cellIDDict3G, cellIDDict4G, cellIDDict5G)

			# Bulk insert leftover documents to Mongo
			self._mongoConnection.executeBulkOperation()

	def enrichDocument(self, mongoDocument, newDocument, hm, cellIDDict2G, cellIDDict3G, cellIDDict4G, cellIDDict5G):

		try:
			if newDocument["CLASS"]=="LNCEL" or newDocument["CLASS"]=="NRCELL":
				if 'NAME' not in newDocument.keys():
					newDocument["NAME"]=newDocument["CELLNAME"]
		except:
			#logger.warning("ERROR FDN {0} ".format(newDocument["DISTNAME"]))
			pass

		hm.addManagedObject(newDocument)

		for key, value in [(x.split("-")[0],x.split("-")[1]) for x in newDocument["DISTNAME"].split("/")]:
			if key.upper() == "PLMN": continue
			newDocument[key.upper()] = value
			mongoDocument[key.upper()] = value

		for pKey, pName in hm.getParents(newDocument["DISTNAME"]).items():
			newDocument[pKey] = pName
			mongoDocument[pKey] = pName

		measUnitID = newDocument["CLASS"]

		#Add an attribute "name_of_MO_type_NAME"
		if "NAME" in newDocument:
			newDocument[measUnitID + "_NAME"] = newDocument["NAME"]
			mongoDocument[measUnitID + "_NAME"] = newDocument["NAME"]

		#2G
		if newDocument["CLASS"] == "BTS":
			if "CELL_NAME" not in mongoDocument:
				if "NAME" in newDocument:
					mongoDocument["CELL_NAME"] = newDocument["NAME"]
					mongoDocument["CELLNAME"] = newDocument["NAME"]
			####
			if "NAME" in newDocument and newDocument["NAME"] != "":
				mongoDocument["BTS_NAME"] = newDocument["NAME"]
				newDocument["BTS_NAME"] = newDocument["NAME"]
			elif "SEGMENTNAME" in newDocument and newDocument["SEGMENTNAME"] != "":
				mongoDocument["BTS_NAME"] = newDocument["SEGMENTNAME"]
				newDocument["BTS_NAME"] = newDocument["SEGMENTNAME"]
			else:
				if "NWNAME" in newDocument:
					if newDocument["NWNAME"] != "":
						mongoDocument["BTS_NAME"] = newDocument["NWNAME"]
						newDocument["BTS_NAME"] = newDocument["NWNAME"]
		if "BSC_NAME" in mongoDocument and "BCF_NAME" in mongoDocument and "BTS_NAME" in mongoDocument:
			if mongoDocument["BTS_NAME"] in cellIDDict2G.keys():
				mongoDocument["CELL_NAME"] = mongoDocument["BTS_NAME"]
				mongoDocument["CELL_ID"] = cellIDDict2G[mongoDocument["BTS_NAME"]]
				mongoDocument["CELLNAME"] = mongoDocument["BTS_NAME"]
				mongoDocument["CELLID"] = cellIDDict2G[mongoDocument["BTS_NAME"]]
			else:
				logger.warning("ERROR: Cant enrich cellname and cellid for BTS_NAME = {}".format(mongoDocument["BTS_NAME"]))

		if "BCF" in newDocument["DISTNAME"]:
			if "BCF_NAME" in mongoDocument.keys() or "BCF_NAME" in newDocument.keys():
				mongoDocument["BTS_NAME"] = mongoDocument["BCF_NAME"]
		#       newDocument["BTS_NAME"] = newDocument["BCF_NAME"]

		#3G
		if newDocument["CLASS"] == "WCEL":
			if "CELL_NAME" not in mongoDocument:
				if "NAME" in newDocument:
					mongoDocument["CELL_NAME"] = newDocument["NAME"]
					mongoDocument["CELLNAME"] = newDocument["NAME"]
			if "CELL_ID" not in mongoDocument or "CELLID" not in mongoDocument:
				if "CID" in newDocument:
					mongoDocument["CELL_ID"] = newDocument["CID"]
					mongoDocument["CELLID"] = newDocument["CID"]
		distmatch = re.match("^(PLMN-PLMN/RNC-\d+/WBTS-\d+/WCEL-\d+).*$", newDocument["DISTNAME"])
		if distmatch != None:
			forkey = distmatch.group(1)

			if forkey in cellIDDict3G.keys():
				#enrich with the CELL_NAME and CELL_ID
				if "CELL_NAME" not in mongoDocument:
					mongoDocument["CELL_NAME"] = cellIDDict3G[forkey][1]
					mongoDocument["CELL_ID"] = cellIDDict3G[forkey][0]
					mongoDocument["CELLNAME"] = cellIDDict3G[forkey][1]
					mongoDocument["CELLID"] = cellIDDict3G[forkey][0]

				#check if there are any subfamilies in the document
				for element in newDocument.keys():
					try:
						#check if it is not a string
						assert not isinstance(newDocument[element], basestring)
						#only reaches this point if it is a list
						#Iterate every dict inside the list (might just be one)
						for subdict in newDocument[element]:
							subdict["CELL_NAME"] = cellIDDict3G[forkey][1]
							subdict["CELL_ID"] = cellIDDict3G[forkey][0]
							subdict["CELLNAME"] = cellIDDict3G[forkey][1]
							subdict["CELLID"] = cellIDDict3G[forkey][0]
					except AssertionError:
						#It's a string, so keep checking
						continue
					except TypeError:
						#It's not a list of dictionaries, but a list of strings, so keep checking
						continue
			else:
				logger.warning("WARNING: Cant enrich cellname and cellid for DISTNAME = {}".format(newDocument["DISTNAME"]))
			return

		#4G
		if newDocument["CLASS"] == "LNBTS":
			if "LNBTS_NAME" not in newDocument and "ENBNAME" in newDocument.keys() and newDocument["ENBNAME"] != '':
				newDocument["LNBTS_NAME"] = newDocument["ENBNAME"]
				mongoDocument["LNBTS_NAME"] = newDocument["ENBNAME"]
			if "LNBTS_NAME" not in newDocument and "MRBTS_NAME" in newDocument.keys() and newDocument["MRBTS"] == newDocument["LNBTS"]:
				newDocument["LNBTS_NAME"] = newDocument["MRBTS_NAME"]
				mongoDocument["LNBTS_NAME"] = mongoDocument["MRBTS_NAME"]
			else:
				pass
		if newDocument["CLASS"] == "LNCEL":
			if "LNBTS_NAME" not in newDocument and "MRBTS_NAME" in newDocument.keys() and newDocument["MRBTS"] == newDocument["LNBTS"]:
					newDocument["LNBTS_NAME"] = newDocument["MRBTS_NAME"]
					mongoDocument["LNBTS_NAME"] = mongoDocument["MRBTS_NAME"]
			else:
				pass
			if "CELL_NAME" not in mongoDocument:
				if "NAME" in newDocument:
					mongoDocument["CELL_NAME"] = newDocument["NAME"]

			if "CELL_NAME" not in newDocument:
				if "CELLNAME" in newDocument:
					newDocument["CELL_NAME"] = newDocument["CELLNAME"]

		distmatch = re.match("^(PLMN-PLMN/MRBTS-\d+/LNBTS-\d+/LNCEL-\d+).*$", newDocument["DISTNAME"])
		if distmatch != None:
			forkey = distmatch.group(1)

			if forkey in cellIDDict4G.keys():
				#enrich with the CELL_NAME and CELL_ID
				if "CELL_NAME" not in mongoDocument:
					mongoDocument["CELL_NAME"] = cellIDDict4G[forkey][1]
					mongoDocument["CELL_ID"] = cellIDDict4G[forkey][0]
					mongoDocument["CELLNAME"] = cellIDDict4G[forkey][1]
					mongoDocument["CELLID"] = cellIDDict4G[forkey][0]

				#check if there are any subfamilies in the document
				for element in newDocument.keys():
					try:
						#check if it is not a string
						assert not isinstance(newDocument[element], basestring)
						#only reaches this point if it is a list
						#Iterate every dict inside the list (might just be one)
						for subdict in newDocument[element]:
							subdict["CELL_NAME"] = cellIDDict4G[forkey][1]
							subdict["CELL_ID"] = cellIDDict4G[forkey][0]
							subdict["CELLNAME"] = cellIDDict4G[forkey][1]
							subdict["CELLID"] = cellIDDict4G[forkey][0]

					except AssertionError:
						#It's a string, so keep checking
						#logger.warning("AssertionError")
						continue
					except TypeError:
						#It's not a list of dictionaries, but a list of strings, so keep checking
						#logger.warning("TypeError")
						continue
			else:
				#logger.warning("WARNING: Cant enrich cellname and cellid for DISTNAME = {0} in unit {1}".format(newDocument["DISTNAME"],newDocument["CLASS"]))
				pass
			return


		#5G

		if newDocument["CLASS"] == "NRBTS":
			if "NRBTS_NAME" not in newDocument and "MRBTS_NAME" in newDocument.keys() and newDocument["MRBTS"] == newDocument["NRBTS"]:
				newDocument["NRBTS_NAME"] = newDocument["MRBTS_NAME"]
				mongoDocument["NRBTS_NAME"] = mongoDocument["MRBTS_NAME"]
			else:
				pass

		if newDocument["CLASS"] == "NRCELL":
			if "NRBTS_NAME" not in newDocument and "MRBTS_NAME" in newDocument.keys() and newDocument["MRBTS"] == newDocument["NRBTS"]:
				newDocument["NRBTS_NAME"] = newDocument["MRBTS_NAME"]
			else:
				pass
			if "CELL_NAME" not in mongoDocument:
				if "CELLNAME" in newDocument:
					mongoDocument["CELL_NAME"] = newDocument["CELLNAME"]
			if "CELL_NAME" not in newDocument:
				if "CELLNAME" in newDocument:
					newDocument["CELL_NAME"] = newDocument["CELLNAME"]
					newDocument["NRCELL_NAME"] = newDocument["CELLNAME"]
					mongoDocument["CELL_NAME"] = newDocument["CELLNAME"]
					mongoDocument["NRCELL_NAME"] = newDocument["CELLNAME"]

		distmatch = re.match("^(PLMN-PLMN/MRBTS-\d+/NRBTS-\d+/NRCELL-\d+).*$", newDocument["DISTNAME"])
		if distmatch != None:
			forkey = distmatch.group(1)

			if forkey in cellIDDict5G.keys():
				#enrich with the CELL_NAME and CELL_ID
				if "CELL_NAME" not in mongoDocument:
					mongoDocument["CELL_NAME"] = cellIDDict5G[forkey][1]
					mongoDocument["CELL_ID"] = cellIDDict5G[forkey][0]
					mongoDocument["CELLNAME"] = cellIDDict5G[forkey][1]
					mongoDocument["CELLID"] = cellIDDict5G[forkey][0]

				#check if there are any subfamilies in the document
				for element in newDocument.keys():
					try:
						#check if it is not a string
						assert not isinstance(newDocument[element], basestring)
						#only reaches this point if it is a list
						#Iterate every dict inside the list (might just be one)
						for subdict in newDocument[element]:
							subdict["CELL_NAME"] = cellIDDict5G[forkey][1]
							subdict["CELL_ID"] = cellIDDict5G[forkey][0]
							subdict["CELLNAME"] = cellIDDict5G[forkey][1]
							subdict["CELLID"] = cellIDDict5G[forkey][0]

					except AssertionError:
						#It's a string, so keep checking
						#logger.warning("AssertionError")
						continue
					except TypeError:
						#It's not a list of dictionaries, but a list of strings, so keep checking
						#logger.warning("TypeError")
						continue
			else:
				#logger.warning("WARNING: Cant enrich cellname and cellid for DISTNAME = {0} in unit {1}".format(newDocument["DISTNAME"],newDocument["CLASS"]))
				pass
			return



	def fast_iter(self, filePath, familyObj, baseObject, cellIDDict2G, cellIDDict3G, cellIDDict4G, cellIDDict5G):
		context = iter(etree.iterparse(filePath, events=('start', 'end')))
		# get root element
		_, root = next(context)

		tag = ['log', 'managedObject', 'list', 'item', 'p']

		if isinstance(tag, list):
			multi = True
		else:
			multi = False

		newDocument = dict()
		newDocumentItemsList = list()
		itemValues = dict()
		isItemList = False
		listName = ''
		counterNumber = 0
		hm = HierarchyManager.HierarchyManager()

		nDocuments = 0

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
					if elem.tag == namespace + 'log':
						dateTime = (elem.get('dateTime').split('.')[0]).replace('T', ' ')
						elem.clear()

					elif elem.tag == namespace + 'managedObject':
						newDocument['CLASS'] = elem.get('class')
						newDocument['VERSION']  = elem.get('version')
						newDocument['DISTNAME'] = elem.get('distName')
						newDocument['ID'] = elem.get('id')
						newDocument['DATETIME'] = dateTime
						newDocument['INTERVAL'] = 3600
						elem.clear()

					elif elem.tag == namespace + 'list':
						try:
							listName = elem.get('name').upper()
						except:
							listName = ''
						elem.clear()

					elif elem.tag == namespace + 'item' and listName != '':
						isItemList = True
						elem.clear()

				elif event == 'end':
					if elem.tag == namespace + 'managedObject':
						familyObj.clearDocuments()
						mongoDocument = dict()
						self.enrichDocument(mongoDocument, newDocument, hm, cellIDDict2G, cellIDDict3G, cellIDDict4G, cellIDDict5G)
						# update or insert
						mongoDocument["DISTNAME"] = newDocument['DISTNAME']
						mongoDocument["CORRKEY"] = newDocument['DISTNAME']
						#print mongoDocument
						self._mongoConnection.addBulkOperation({'query': {'CORRKEY': newDocument["DISTNAME"]}, 'set': mongoDocument}, 'upSert')
						nDocuments += 1

						if nDocuments % 1000 == 0:
							self._mongoConnection.executeBulkOperation()
							nDocuments = 0
						#logger.warning(newDocument['CLASS'])
						#logger.warning(newDocument.keys())
						familyObj.setUnitID(newDocument['CLASS'])
						try:
							timestamp = familyObj.parseEnvelopeDataTime(newDocument["DATETIME"])
						except ValueError as e:
							logger.warning("Could not build mediationEnvelope due to {0}: ".format(e), __file__)
							continue

						familyObj.addDocument({"dataTime": timestamp, "granularitySec": 3600, "data": newDocument})
						#print newDocument['CLASS']
						self.nextOp(familyObj = familyObj, baseObject = baseObject)

						if len(newDocumentItemsList) != 0:
							for newDocument in newDocumentItemsList:
								familyObj.clearDocuments()
								tmp = copy.deepcopy(mongoDocument)
								tmp.pop('DISTNAME')
								newDocument.update(tmp)
								familyObj.setUnitID(newDocument['CLASS'])
								familyObj.addDocument({"dataTime": timestamp, "granularitySec": 3600, "data": newDocument})
								self.nextOp(familyObj = familyObj, baseObject = baseObject)

						newDocument = dict()
						newDocumentItemsList = list()

					elif elem.tag == namespace + 'item' and isItemList:
						itemValues['CLASS'] = newDocument['CLASS'] +'_'+ listName.upper()
						if 'VERSION' not in itemValues:
							itemValues['VERSION']  = newDocument['VERSION']
						itemValues['DISTNAME'] = newDocument['DISTNAME'] +'/'+ listName +'-'+ str(counterNumber)
						if 'ID' not in itemValues:
							itemValues['ID'] = newDocument['ID']
						itemValues['DATETIME'] = dateTime
						itemValues['INTERVAL'] = 3600

						newDocumentItemsList.append(itemValues)

						isItemList = False
						itemValues = dict()
						counterNumber += 1

					elif elem.tag == namespace + 'list':
						listName = ''
						counterNumber = 0

					elif elem.tag == namespace + 'p':

						if elem.text != None:
							try:
								value = (elem.text.encode("utf-8")).strip()#.replace('\n', '')
							except Exception as e:
								logger.warning('Error: {0}: '.format(e))
								value = ''
						else:
							value = ''
						if 'name' in elem.attrib.keys():
							if isItemList:
								itemValues[elem.get('name').upper()] = value
							else:
								newDocument[elem.get('name').upper()] = value
						elif listName != '':
							if listName in newDocument.keys():
								newDocument[listName] = newDocument[listName] + ',' + str(value)
							else:
								newDocument[listName] = str(value)

					elem.clear()
			else:
				elem.clear()
		del context

	def enrichData(self, filePath, cellIDDict2G, cellIDDict3G, cellIDDict4G, cellIDDict5G):
		context = iter(etree.iterparse(filePath, events=('start', 'end')))
		# get root element
		_, root = next(context)

		tag = ['managedObject', 'p']

		if isinstance(tag, list):
			multi = True
		else:
			multi = False

		namespace = None
		enrichmentData = dict()
		for event, elem in context:
			if event == 'start' and namespace is None:
				if "}" in elem.tag:
					namespace = elem.tag.split("}")[0].strip("{")
					namespace = "{" + namespace + "}"
				else:
					namespace = ""

			if multi:
				for t in tag:
					if event == 'start' and elem.tag == namespace + t:
						if elem.tag == namespace + 'managedObject':
							moClassName = elem.get('class')
							distName = elem.get('distName')
							elem.clear()

					elif event == 'end' and elem.tag == namespace + t:
						if elem.tag == namespace + 'managedObject':
							#2G
							if moClassName == 'BTS':
								if enrichmentData['cellId'] != '':
									#Different 'Xname' fields have different priorities
									if 'name' in enrichmentData:
										cellIDDict2G[enrichmentData['name']] = enrichmentData['cellId']
									elif 'segmentname' in enrichmentData:
										cellIDDict2G[enrichmentData['segmentname']] = enrichmentData['cellId']
									elif 'segmentName' in enrichmentData:
										cellIDDict2G[enrichmentData['segmentName']] = enrichmentData['cellId']
									elif 'nwname' in enrichmentData:
										cellIDDict2G[enrichmentData['nwname']] = enrichmentData['cellId']
									elif 'nwName' in enrichmentData:
										cellIDDict2G[enrichmentData['nwName']] = enrichmentData['cellId']

							#3G
							elif moClassName == 'WCEL':
								if 'name' in enrichmentData:
									cellIDDict3G[distName] = (enrichmentData['CId'], enrichmentData['name'])
									#print cellIDDict3G[distName]

							#4G
							elif moClassName == 'LNCEL':
								if 'name' in enrichmentData and 'eutraCelId' in enrichmentData:
									cellIDDict4G[distName] = (enrichmentData['eutraCelId'], enrichmentData['name'])
								elif 'cellName' in enrichmentData and 'eutraCelId' in enrichmentData:
									cellIDDict4G[distName] = (enrichmentData['eutraCelId'], enrichmentData['cellName'])

							#4G
							elif moClassName == 'NRCELL':
								if 'cellName' in enrichmentData and 'nrCellIdentity' in enrichmentData:
									cellIDDict5G[distName] = (enrichmentData['nrCellIdentity'], enrichmentData['cellName'])

							moClassName = ''
							distName = ''
							enrichmentData = dict()

						elif elem.tag == namespace + 'p' and 'name' in elem.attrib.keys():
							try:
								enrichmentData[elem.get('name')] = elem.text.replace('\n', '')
							except:
								#logger.warning("ERROR RAFA {0} ".format(elem.get('name')))
								pass
						# preserve memory
						elem.clear()
			else:
				if event == 'end' and elem.tag == namespace + tag:
					# preserve memory
					elem.clear()
		#logger.warning("enrichmentData {0} ".format(enrichmentData)
		del context
