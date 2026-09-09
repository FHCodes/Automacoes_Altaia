__doc__ = \
'''
    Parser for NOKIA CMG PCMD data
'''

__version__ = '0.1'

__authors__ = [
                "Version 1.0: Bruno Silva <bruno-e-silva@alticelabs.com>"
            ]

import re, os, json
#from datetime import datetime, time,timedelta
import importlib

# Local libraries
BaseOperator = importlib.import_module("shelf.collectorprocess.operators.BaseOperator").BaseOperator
FamilyObject = importlib.import_module("shelf.collectorprocess.operators.FamilyObject").FamilyObject
logger = importlib.import_module("shelf.collectorprocess.logger").logger

class Operator(BaseOperator):

	def __init__(self, operation, baseObject={}):
		BaseOperator.__init__(self, operation, baseObject=baseObject)
		self._peerNodeIPRegex = re.compile(r'(^\d+.\d+.\d+.\d+$)|(^$)')
		self._peerNodeRegex = re.compile(r'^\d+')

	def process(self, familyObj=FamilyObject(), baseObject={}):

		logger.debug("[Reader] Reading PER CALL MEASUREMENT DATA CSV files contents...")

		config = None
		replaceDict = json.load(open('/opt/alticelabs/namf/src/shelf/collectorprocess/operators/Readers/NOKIA/CSV/PCMD/replaceDictionary.json'))

		filesToBeProcessed = familyObj.getFiles()

		familyObj.clearFiles()
		familyObj = familyObj

		rt = re.compile(r'_\d+$')

		for filePath in filesToBeProcessed:
			try:
				self.fileName = os.path.basename(filePath)

				#leitura de linhas, implementar com while
				fp = open(filePath)
				lines = fp.readlines()
				fp.close()
				config = None
				for line in lines:
					self.data = (line.strip('\n'))[2:-1].split(';')
					if self.data[-1].endswith('%'):
						self.data[-1] = self.data[-1].replace('%','')
					if config == None:
						try:
							config = json.load(open('/opt/alticelabs/namf/src/shelf/collectorprocess/operators/Readers/NOKIA/CSV/PCMD/configs/version{0}.json'.format(self.data[0])))
							self.format = config['format']
						except:
							logger.warning('PCMDVERSION "{0}" not supported'.format(self.data[0]))
							break

					header = dict(zip(config['header']['items'],self.data[:2]))
					self.data = self.data[2:]

					stuff = FamilyObject()
					stuff.fileName = self.fileName
					stuff.setUnitID(config[header['RECORDTYPE']]['name'])
					newDocument = self.readContainer(header,config[header['RECORDTYPE']])

					for key in newDocument.keys():
						if re.search(rt, key) != None:
							tmp = key.split('_')
							nkey = tmp[0]+'_'
							value = tmp[1]
						else:
							nkey = key
							value = ''

						if nkey in replaceDict.keys():
							item = replaceDict[nkey][newDocument[key]]
							for fkey in item.keys():
								newDocument[fkey+value] = item[fkey]

						if config[header['RECORDTYPE']]['name'] == 'CMG_CData' and 'TRIGGERTYPENAME' not in newDocument:
							newDocument['TRIGGERTYPENAME'] = '-'

					if 'MSISDN' in newDocument.keys():
						newDocument['NDC'] = newDocument['MSISDN'][2:4]
					if 'IMEI' in newDocument.keys():
						newDocument['TAC'] = newDocument['IMEI'][:8]

					try:
						timestamp = familyObj.parseEnvelopeDataTime(newDocument["PROCEDURESTARTTIME"])
					except ValueError as e:
						logger.warning("Could not build mediationEnvelope due to {0}: ".format(e), __file__)
						continue

					stuff.addDocument({"dataTime": timestamp, "granularitySec": 120, "data": newDocument})
					self.nextOp(familyObj=stuff, baseObject=baseObject)

				del lines
			except Exception as ex:
				logger.error("Exception occurred on file '{0}', due to {1}".format(os.path.basename(filePath), ex))

	def pop(self):
		item = self.data[0]
		self.data.remove(item)
		return item

	def readContainer(self,newDocument,config):
		i = 1
		for item in config['items']:
			if len(self.data) == 0:
				return newDocument

			item = item.upper()

			if item == 'SERVICEUSAGEDURATION':
				t1 = newDocument['ENDTIME']
				t2 = newDocument['STARTTIME']
				newDocument[item] = (int(t1[11:13])*3600+int(t1[14:16])*60+int(t1[17:19])) - (int(t2[11:13])*3600+int(t2[14:16])*60+int(t2[17:19]))
				continue
			elif item == 'SERVICESTARTEDDURATION':
				t1 = newDocument['PROCEDURESTARTTIME']
				t2 = newDocument['STARTTIME']
				newDocument[item] = (int(t1[11:13])*3600+int(t1[14:16])*60+int(t1[17:19])) - (int(t2[11:13])*3600+int(t2[14:16])*60+int(t2[17:19]))
				continue
			elif item in self.format:
				newDocument[item] = self.timeStampConvert(self.pop())
			else:
				newDocument[item] = self.pop()

			if "NUMBEROF" in item:
				try:
					nContainer = int(newDocument[item])
					if nContainer > 0:
						for container in config['containers']:
							if container['parentItem'] == item:

								nid = 1

								while nid <= nContainer:
									for cItem in container['items']:
										cItem = cItem.upper()
										if cItem in self.format:
											newDocument[cItem+'_'+str(nid)] = self.timeStampConvert(self.pop())
										else:
											newDocument[cItem+'_'+str(nid)] = self.pop()
									nid += 1

								nid = 1
								while nid <= nContainer:
									for cItem in container['extended_items']:
										newDocument[cItem+'_'+str(nid)] = self.pop()
									nid += 1
				except Exception as e:
					print e
			elif item == 'UEID':
				newDocument['MCC'] = newDocument['UEID'][0:3]
				newDocument['MNC'] = newDocument['UEID'][3:6]

			if item == 'MSISDN' and newDocument['PCMDVERSION'] in [5, '5']:
				while True:
					if self._peerNodeIPRegex.match(self.data[1]) and self._peerNodeRegex.match(self.data[0]):
						newDocument['PEER{0}TYPE'.format(i)] = self.pop()
						newDocument['PEER{0}TYPEIP'.format(i)] = self.pop()
						i += 1
					else:
						break

		return newDocument

	def timeStampConvert(self,item):
		return re.sub(r'\.',' ',item[0:19])
