__doc__ = \
'''
	
'''

__version__ = '0.1'

__authors__ = [
				"Version 1.0: Bruno Silva <bruno-e-silva@alticelabs.com>"
			]

import sys, re, os, json
import datetime
from xml.sax import saxutils, handler, make_parser, parse
import argparse

class NokiaParameterPreParser(handler.ContentHandler):

	def __init__(self, fileName, outdir, configsDir, verbose):
		self._header = '<?xml version="1.0" encoding="UTF-8"?>'
		self._footer = ''
		self._toWrite = ''
		self._techFileList = dict()
		self._fileList = list()
		self._tech = ''
		self._outdir = outdir
		self._fileName = fileName
		self._config = dict()
		self._configFile = ''
		self._distName = ''
		self._readHeader = True
		self._verbose = verbose

		if configsDir == '':
			configsDir = '/opt/alticelabs/namf/tools/Configs/Nokia_preParser/'
			configFiles = [configsDir + f for f in os.listdir(configsDir) if os.path.isfile(configsDir + f) and re.match(r'^.*.json', f)]
			for jsonFile in configFiles:
				keyName = (os.path.basename(jsonFile)).replace('.json','')
				self._config[keyName] = json.load(open(jsonFile))
		else:
			keyName = (os.path.basename(configsDir)).replace('.json','')
			self._config[keyName] = json.load(open(configsDir))

	
	def startDocument(self):
		self._startTime = datetime.datetime.now()

	def endDocument(self):
		print ("----- END_PROCESSING_FILE: {:20s}   END_TIME: {:s}   DURATION: {:s} -".format(self._fileName, str(datetime.datetime.now()), str(datetime.datetime.now()-self._startTime)))

		fileList = list()
		for tech in self._techFileList.keys():
			if self._techFileList[tech]['fileName'] not in fileList:
				f = open(self._techFileList[tech]['fileName'], 'a+')
				f.write(self._footer)
				f.close()
				fileList.append(self._techFileList[tech]['fileName'])

	def startElement(self, name, attrs):

		if name in ['header', 'log', 'raml', 'cmData']:
			self._readHeader = True
			self._header += '<{0}'.format(name)
			if name != 'raml':
				for attr in attrs.keys():
					self._header += ' {0}="{1}"'.format(attr, attrs[attr])
			self._header += '>'

		elif name == 'managedObject':
			self._readHeader = False
			try:
				self._tech = (re.search('PLMN-([^\/]*)/(?P<tech>[^\/]*)-.*$', attrs['distName'])).group('tech')
				for configFile in self._config.keys():
					if self._tech in self._config[configFile].keys():
						self._toWrite = '<{0}'.format(name)
						for attr in attrs.keys():
							self._toWrite += ' {0}="{1}"'.format(attr, attrs[attr])
						self._toWrite += '>\n'
						self._configFile = configFile
						self._distName = attrs['distName']
						break
			except Exception as e:
				print ('[Flushed]{:s};{:s};{:s}'.format(attrs['class'], self._distName, self._fileName))
				self._toWrite = ''

		elif name in ['p', 'list', 'item']:
			if self._toWrite != '':
				self._toWrite += '<{0}'.format(name)
				for attr in attrs.keys():
					self._toWrite += ' {0}="{1}"'.format(attr, attrs[attr])
				self._toWrite += '>'

	def endElement(self, name):
		#_, name = name

		if name in ['managedObject', 'p', 'list', 'item'] and self._toWrite != '':
			self._toWrite += '</{0}>\n'.format(name)
			if name == 'managedObject':
				#escrever para ficheiro
				if self._tech not in self._techFileList.keys():
					self._techFileList[self._tech] = dict()
					self._techFileList[self._tech]['fileName'] = '{0}{1}_{2}'.format(self._outdir, self._configFile, self._fileName)
					if self._techFileList[self._tech]['fileName'] not in self._fileList:
						self._fileList.append(self._techFileList[self._tech]['fileName'])
						if os.path.exists(self._techFileList[self._tech]['fileName']):
							print ('[Warning] Removing already existing file: {0}'.format(os.path.basename(self._techFileList[self._tech]['fileName'])))
							os.remove(self._techFileList[self._tech]['fileName'])
						f = open(self._techFileList[self._tech]['fileName'], 'a+')
						self._toWrite = '{0}{1}'.format(self._header, self._toWrite)
					else:
						f = open(self._techFileList[self._tech]['fileName'], 'a+')
				else:
					f = open(self._techFileList[self._tech]['fileName'], 'a+')

				f.write(self._toWrite)
				f.close()
				
				if self._verbose:
					print ('{:s};{:s};{:s}'.format(self._tech, self._distName, os.path.basename(self._techFileList[self._tech]['fileName'])))
				self._toWrite = ''

		elif name in ['header', 'log']:
			self._header += '</{0}>\n'.format(name)
		elif name in ['raml', 'cmData']:
			self._footer += '</{0}>\n'.format(name)

	def characters(self, content):
		try:
			content = saxutils.escape(content.encode("utf-8"))
			if self._toWrite != '' and not re.match('^.*<\\[^>]*>$', self._toWrite) and not self._header.endswith('/>'):
				self._toWrite += (content if content.strip() != '' else '')
			elif self._header != '' and self._readHeader:
				self._header += (content if content.strip() != '' else '')
		except:
			print ('[Error]{:s};{:s};{:s}'.format(attrs['class'], self._distName, self._fileName))

	def unparsedEntityDecl(self, name, publicId, systemId, ndata):
		pass

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='Pre Parser Nokia Parameter files.')
	parser.add_argument('-indir', help='the input directory')
	parser.add_argument('-outdir', help='the output directory')
	parser.add_argument('-config', default='', help='config file')
	parser.add_argument('-verbose', default='v', help='verbose (v,vv)')
	args = parser.parse_args()

	verbose = False
	if re.match('^vv+$', args.verbose):
		verbose = True
	
	if not os.path.exists(args.indir):
		print ('[Critical] Input directory doesnt exist: {0}'.format(args.indir))
		sys.exit()
	
	if not os.path.exists(args.outdir):
		print ('[Critical] Onput directory doesnt exist: {0}'.format(args.outdir))
		sys.exit()

	if not os.path.exists(args.config) and args.config != '':
		print ('[Critical] Configuration file doesnt exist: {0}'.format(args.config))
		sys.exit()
	
	startTime = datetime.datetime.now()
	print ("------------------------------------------------------------------------------------")
	print ("--------- SCRIPT START                -----> {0}    ---------".format(str(startTime)))
	print ("--------- IN DIRECTORY: {:51} ---------".format(args.indir))
	print ("--------- OUTPUT DIRECTORY: {:47} ---------".format(args.outdir))
	if args.config != '':
		print ("--------- CONFIG FILE: {:52} ---------".format(args.config))
	print ("------------------------------------------------------------------------------------")
	
	filesToProcess = [args.indir + f for f in os.listdir(args.indir) if os.path.isfile(args.indir + f)]
	for fileName in filesToProcess:
		if not fileName.endswith('xml'):
			print ('[Warning] File type unknown: {0}'.format(os.path.basename(fileName)))
			continue
		
		print ("----- START_PROCESSING_FILE: {:30s}  TIME: {:s} -".format(os.path.basename(fileName), str(datetime.datetime.now())))
		try:
			erichandler = NokiaParameterPreParser(os.path.basename(fileName), args.outdir, args.config, verbose)
			xml_parser = make_parser()
			# Set the custom handler as the parser's handler
			xml_parser.setContentHandler(erichandler)
			xml_parser.setFeature(handler.feature_external_ges, False)
			xml_parser.setFeature(handler.feature_namespaces, False)
			xml_parser.parse(fileName)
		except Exception as e:
			print ('[Error] Exception in file {0}: {1}'.format(os.path.basename(fileName), e))

	endTime = datetime.datetime.now()
	print ("------------------------------------------------------------------------------------")
	print ("--------- SCRIPT END                    -----> {0}  ---------".format(str(endTime)))
	print ("--------- TOTAL DURATION                 ----->      {0}        ---------".format(endTime-startTime))
	print ("------------------------------------------------------------------------------------")
