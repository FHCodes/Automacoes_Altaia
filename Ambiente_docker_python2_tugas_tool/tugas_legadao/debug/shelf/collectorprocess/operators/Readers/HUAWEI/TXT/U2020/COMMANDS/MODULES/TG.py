#!/usr/bin/env python

__version__ = '1.0'

__doc__ = '''
Example file:

LST TG:MSF=MASTER;
SX-VMA50
+++	AGCF/*MEID:281 MENAME:SX-VMA50*/		2018-06-13 12:04:18-03:00
O&M	#184446
%%/*1567098 MEID=281*/LST TG: MSF=MASTER;%%
RETCODE = 0  Operation succeeded

No7 Trunk Group
---------------
 Trunk group number  Trunk group name  OPC	 DPC	 Network Indicator  Master/Slave flag

 1				   0T00SPO_04007U	000C3B  000FA7  National network   Master
(Number of results = 1)

---	END
+++	AGCF/*MEID:281 MENAME:SX-VMA50*/		2018-06-13 12:04:18-03:00
O&M	#184446
%%/*1567098 MEID=281*/LST TG: MSF=MASTER;%%
RETCODE = 0  Operation succeeded
No7 Trunk Group (Continue)
--------------------------
 Trunk group number  Circuit type  Group direction	   Sub-route number  Sub-route name	 Master/Slave flag

 1				   ISUP		  Bi-directional trunk  1				 0T00SPO_04007U  Master
(Number of results = 1)
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
		self._command_name_regex = re.compile(r'LST TG:')
		self._command_name = 'TG'
		self._lineSepRegex = re.compile(r'\s{2,}')
		self._startBlockRegex = re.compile(r'^-{1,}[\n|\r]$')
		self._nOfResRegex = re.compile(r'^\(Number of results = \d{1,}\)$')
		self._sswIdRegex = re.compile(r' MENAME:(.+?)\*')

	@property
	def line_format(self):
		return self._line_format

	def parse(self, file_path, lines, commandLine):
		logger.debug("Parsing TG command for U2000 and N2000, in file {0}".format(os.path.basename(file_path)))

		line = lines.pop(0).strip('\n|\r|\t')

		while True:
			if line.startswith('MML Command Report:'):
				line = lines.pop(0).strip('\n|\r|\t')
				if re.search(r'AGCF\/', line) is not None:
					self._command_name = 'SoftX3000_{0}'.format(self._command_name)
					pkField = 'TRUNK GROUP NUMBER'
					break
				elif re.search(r'MSOFTX\/', line) is not None:
					self._command_name = 'MSoftX3000_{0}'.format(self._command_name)
					pkField = 'TRUNK GROUP NAME'
					break
			if line.startswith('===================='):
				return
			line = lines.pop(0).strip('\n|\r|\t')

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
									if document[pkField] not in documentList.keys():
										document['DATETIME'] = date
										document['SSWID'] = SSWID
										documentList[document[pkField]] = document
								except:
									break

						if line.startswith('========================='):
							break
					elif groupName.upper() + ' CONTINUE ' in line.upper() or groupName.upper() + ' (CONTINUE)' in line.upper():
						#atencao as pk
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
									if document[pkField] in documentList.keys():
										documentList[document[pkField]].update(document)
									else:
										logger.warning('PK \"{:s}\" was not found'.format(document[pkField]))
								except:
									break

						if line.startswith('========================='):
							break

					elif groupName != line:
						for docKey in documentList.keys():
							if ('OPC' in documentList[docKey].keys() and 'DPC' in documentList[docKey].keys()) or ('ORIGINATING POINT CODE' in documentList[docKey].keys() and 'DESTINATION POINT CODE' in documentList[docKey].keys()):
								try:
									documentList[docKey]['DESTINATION POINT CODE'] = documentList[docKey]['DESTINATION POINT CODE'].replace("H'", '')
									documentList[docKey]['ORIGINATING POINT CODE'] = documentList[docKey]['ORIGINATING POINT CODE'].replace("H'", '')
								except:
									documentList[docKey]['DPC'] = documentList[docKey]['DPC'].replace("H'", '')
									documentList[docKey]['OPC'] = documentList[docKey]['OPC'].replace("H'", '')
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
									if document[pkField] not in documentList.keys():
										document['DATETIME'] = date
										document['SSWID'] = SSWID
										documentList[document[pkField]] = document
								except:
									break

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
				if ('OPC' in documentList[docKey].keys() and 'DPC' in documentList[docKey].keys()) or ('ORIGINATING POINT CODE' in documentList[docKey].keys() and 'DESTINATION POINT CODE' in documentList[docKey].keys()):
					yield documentList[docKey]

		except IOError:
			logger.error("Could not open sample file {0} in read mode.".format(os.path.basename(file_path)))
