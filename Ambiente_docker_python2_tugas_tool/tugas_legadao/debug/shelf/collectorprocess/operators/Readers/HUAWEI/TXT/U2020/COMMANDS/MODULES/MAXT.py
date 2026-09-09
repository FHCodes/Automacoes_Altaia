#!/usr/bin/env python

__version__ = '1.0'

__doc__ = '''
Example file:
SOFTX:
LST MAXT:TID=TID304,TP=ACU,MN=1000;
SX-VMA50
+++	AGCF/*MEID:281 MENAME:SX-VMA50*/		2018-06-13 13:09:38-03:00
O&M	#184631
%%/*1567230 MEID=281*/LST MAXT: TID=TID304,TP=ACU,MN=1000;%%
RETCODE = 0  Operation succeeded

Maximum number of tuples of private tables
------------------------------------------
		  Table name  =  tbl_TkCircuit
			Table ID  =  304
	   Module number  =  1000
Maximum tuple number  =  33000
		 Used Number  =  31431
(Number of results = 1)

---	END


MSOFTX:
+++	MSOFTX/*MEID:5 MENAME:MX-RJ-ARC70*/		2020-08-11 13:27:09-03:00
O&M	#101874
%%/*2661028 MEID=005 MML Session=1597163227*/LST MAXT: TID=TID304,MT=CCU;%%
RETCODE = 0  Operation succeeded

The maximum number of tuples in the private table
-------------------------------------------------
 Table ID  Table name	 Table description  Module type  Module number  Maximum number of tuples  Used number of tuples  Usage percent

 304	   tbl_TkCircuit  Trk ckt table	  WCCU		 1000		   20000					 930					4.6500%
(Number of results = 1)

---	END
'''

__authors__ = [
				"Version 1.0: bruno-e-silva <bruno-e-silva@alticelabs.com>"
			]

import os
import re
import importlib

# Local libraries
BaseOperator = importlib.import_module("shelf.collectorprocess.operators.BaseOperator").BaseOperator
FamilyObject = importlib.import_module("shelf.collectorprocess.operators.FamilyObject").FamilyObject
BaseCommand = importlib.import_module("shelf.collectorprocess.operators.Readers.HUAWEI.TXT.U2020.COMMANDS.Operator").Command
logger = importlib.import_module("shelf.collectorprocess.logger").logger


# Command class that extends the base command defined in Operator.py
class Command(BaseCommand):

	def __init__(self):
		self._command_name_regex = re.compile(r'LST MAXT')
		self._command_name = 'MAXT'
		self._lineSepRegex = re.compile(r'\s{2,}')
		self._startBlockRegex = re.compile(r'^-{1,}[\n|\r]$')
		self._nOfResRegex = re.compile(r'^\(Number of results = \d{1,}\)$')
		self._dataSepRegex = re.compile(r'^(.+?)  =  (.+?)$')
		self._sswIdRegex = re.compile(r' MENAME:(.+?)\*')

	@property
	def line_format(self):
		return self._line_format

	def parse(self, file_path, lines, commandLine):
		logger.debug("Parsing MAXT command for U2000, in file {0}".format(os.path.basename(file_path)))

		line = lines.pop(0).strip('\n|\r|\t')
		while True:
			if line.startswith('MML Command Report:'):
				line = lines.pop(0).strip('\n|\r|\t')
				if re.search(r'AGCF\/', line) is not None:
					self._command_name = 'SoftX3000_{0}'.format(self._command_name)
					for document in self.softX(file_path, line, lines, commandLine):
						yield document
					return
				elif re.search(r'MSOFTX\/', line) is not None:
					self._command_name = 'MSoftX3000_{0}'.format(self._command_name)
					for document in self.mSoftX(file_path, line, lines, commandLine):
						yield document
					return
			if line.startswith('===================='):
				return
			line = lines.pop(0).strip('\n|\r|\t')

	def softX(self, file_path, line, lines, commandLine):
		try:
			groupName = ''
			documentList = dict()
			toBeContinued = False

			while len(lines) > 0 and not line.startswith('========================='):
				document = dict()

				if line.startswith('+++'):
					values = re.split(self._lineSepRegex, line.strip())
					try:
						SSWID = re.search(self._sswIdRegex, values[1]).group(1)
					except:
						SSWID = values[1]
					date = self.convert_datestring(values[2])

					line = lines.pop(0).strip('\n|\r|\t')

				elif re.search(self._startBlockRegex, lines[0]) is not None:

					if (toBeContinued and groupName == line) or groupName == '':
						groupName = line
						lines.pop(0)

						while len(lines) > 0 and not line.startswith('========================='):
							line = lines.pop(0).strip('\n|\r| |\t')
							if line in ['', 'To be continued...']:
								break
							elif re.search(self._nOfResRegex, line) is not None:
								if document['MODULE NUMBER'] not in documentList.keys():
									document['DATETIME'] = date
									document['MENAME'] = SSWID
									documentList[document['MODULE NUMBER']] = document
								break
							else:
								lineParsed = re.search(self._dataSepRegex, line)
								if lineParsed.group(1).upper() not in document.keys():
									document[lineParsed.group(1).upper()] = lineParsed.group(2)

						if line.startswith('========================='):
							break
					elif (groupName + ' (Continue)') == line:
						#atencao as pk
						lines.pop(0)

						while len(lines) > 0 and not line.startswith('========================='):
							line = lines.pop(0).strip('\n|\r|\t')
							if line in ['', 'To be continued...']:
								break
							elif re.search(self._nOfResRegex, line) is not None:
								if document['MODULE NUMBER'] in documentList.keys():
									documentList[document['MODULE NUMBER']].update(document)
								break
							else:
								line = re.search(self._dataSepRegex, line)
								if line.group(1).upper() not in document.keys():
									document[line.group(1).upper()] = line.group(2)

						if line.startswith('========================='):
							break
					elif groupName != line:
						for docKey in documentList.keys():
							yield documentList[docKey]
						documentList = dict()

						groupName = line
						lines.pop(0)

						while len(lines) > 0 and not line.startswith('========================='):
							line = lines.pop(0).strip('\n|\r|\t')
							if line in ['', 'To be continued...']:
								break
							elif re.search(self._nOfResRegex, line) is not None:
								if document['MODULE NUMBER'] not in documentList.keys():
									document['DATETIME'] = date
									document['MENAME'] = SSWID
									documentList[document['MODULE NUMBER']] = document
								break
							else:
								line = re.search(self._dataSepRegex, line)
								if line.group(1).upper() not in document.keys():
									document[line.group(1).upper()] = line.group(2)

						if line.startswith('========================='):
							break

					toBeContinued = False
					while len(lines) > 0 and not line.startswith('========================='):
						if re.search(self._startBlockRegex, lines[0]) is not None:
							break
						elif line == 'To be continued...':
							toBeContinued = True
							line = lines.pop(0).strip('\n|\r|\t')
						elif re.search(r'^---	END$', line) is not None:
							line = lines.pop(0).strip('\n|\r|\t')
							break
						elif line.startswith('---	END'):
							line = line.replace('---	END', '')
							break
						else:
							line = lines.pop(0).strip('\n|\r|\t')
					if line.startswith('========================='):
						break
				else:
					line = lines.pop(0).strip('\n|\r|\t')

			for docKey in documentList.keys():
				yield documentList[docKey]

		except IOError:
			logger.error("Could not open sample file {0} in read mode.".format(os.path.basename(file_path)))

	def mSoftX(self, file_path, line, lines, commandLine):

		try:
			groupName = ''
			documentList = dict()
			toBeContinued = False

			while len(lines) > 0 and not line.startswith('========================='):

				if line.startswith('+++'):
					values = re.split(self._lineSepRegex, line.strip())
					try:
						SSWID = re.search(self._sswIdRegex, values[1]).group(1)
					except:
						SSWID = values[1]
					date = self.convert_datestring(values[2])

					line = lines.pop(0).strip('\n|\r|\t')

				elif re.search(self._startBlockRegex, lines[0]) is not None:

					if (toBeContinued and groupName == line) or groupName == '':
						groupName = line
						lines.pop(0)
						header = re.split(self._lineSepRegex, (lines.pop(0).upper()).strip())
						lines.pop(0)

						while len(lines) > 0 and not line.startswith('========================='):
							line = lines.pop(0).strip('\n|\r|\t')
							if line in ['', 'To be continued...']:
								break
							elif re.search(self._nOfResRegex, line) is not None:
								break
							else:
								counters = re.split(self._lineSepRegex, line.strip())
								try:
									document = dict(zip(header,counters))
									if document['MODULE NUMBER'] not in documentList.keys():
										document['DATETIME'] = date
										document['MENAME'] = SSWID
										if 'USAGE PERCENT' in document.keys():
											document['USAGE PERCENT'] = re.sub(r' |%', '', document['USAGE PERCENT'])
										documentList[document['MODULE NUMBER']] = document
								except:
									break

					elif (groupName + ' (Continue)') == line:
						#atencao as pk
						lines.pop(0)
						header = re.split(self._lineSepRegex, (lines.pop(0).upper()).strip())
						lines.pop(0)

						while len(lines) > 0 and not line.startswith('========================='):
							line = lines.pop(0).strip('\n|\r')
							if line in ['', 'To be continued...']:
								break
							elif re.search(self._nOfResRegex, line) is not None:
								break
							else:
								counters = re.split(self._lineSepRegex, line.strip())
								try:
									document = dict(zip(header,counters))
									if document['MODULE NUMBER'] in documentList.keys():
										if 'USAGE PERCENT' in document.keys():
											document['USAGE PERCENT'] = re.sub(r' |%', '', document['USAGE PERCENT'])
										documentList[document['MODULE NUMBER']].update(document)
									else:
										logger.warning('PK \"{:s}\" was not found'.format(document['MODULE NUMBER']))
								except:
									break

					elif groupName != line:
						for docKey in documentList.keys():
							yield documentList[docKey]
						documentList = dict()

						groupName = line
						lines.pop(0)
						header = re.split(self._lineSepRegex, (lines.pop(0).upper()).strip())
						lines.pop(0)

						while len(lines) > 0 and not line.startswith('========================='):
							line = lines.pop(0).strip('\n|\r|\t')
							if line in ['', 'To be continued...']:
								break
							elif re.search(self._nOfResRegex, line) is not None:
								break
							else:
								counters = re.split(self._lineSepRegex, line.strip())
								try:
									document = dict(zip(header,counters))
									if document['MODULE NUMBER'] not in documentList.keys():
										document['DATETIME'] = date
										document['MENAME'] = SSWID
										if 'USAGE PERCENT' in document.keys():
											document['USAGE PERCENT'] = re.sub(r' |%', '', document['USAGE PERCENT'])
										documentList[document['MODULE NUMBER']] = document
								except:
									break

					toBeContinued = False
					while len(lines) > 0 and not line.startswith('========================='):
						if re.search(self._startBlockRegex, lines[0]) is not None:
							break
						elif line == 'To be continued...':
							toBeContinued = True
							line = lines.pop(0).strip('\n|\r|\t')
						elif re.search(r'^---	END$', line) is not None:
							line = lines.pop(0).strip('\n|\r|\t')
							break
						elif line.startswith('---	END'):
							line = line.replace('---	END', '')
							break
						else:
							line = lines.pop(0).strip('\n|\r|\t')
				else:
					line = lines.pop(0).strip('\n|\r|\t')

			for docKey in documentList.keys():
				yield documentList[docKey]

		except IOError:
			logger.error("Could not open sample file {0} in read mode.".format(os.path.basename(file_path)))
