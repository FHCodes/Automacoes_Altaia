#!/usr/bin/env python

__doc__ = \
	'''
	OI HUAWEI_COMMANDS_PM files parser manager
'''

__version__ = '1.0'

__authors__ = [
	"Version 1.0: Bruno Silva <bruno-e-silva@alticelabs.com>"
]

import os
import pkgutil
import time
import importlib
import tarfile

# Local libraries
BaseOperator = importlib.import_module("shelf.collectorprocess.operators.BaseOperator").BaseOperator
FamilyObject = importlib.import_module("shelf.collectorprocess.operators.FamilyObject").FamilyObject
MODULES = importlib.import_module("shelf.collectorprocess.operators.Readers.HUAWEI.TXT.U2020.COMMANDS.MODULES")
logger = importlib.import_module("shelf.collectorprocess.logger").logger

# This class represents a command processor. Each command must extend this class
class Command(object):

	def __init__(self):

		self._command_name = None
		self._command_name_regex = None

	@property
	def command_name_regex(self):
		return self._command_name_regex

	@property
	def command_name(self):
		return self._command_name

	@staticmethod
	def convert_datestring(s, pattern='%Y-%m-%d %H:%M:%S', out_pattern='%Y-%m-%d %H:%M:%S'):
		try:
			time_string = time.strftime(out_pattern, time.strptime(s[:19], pattern))
		except ValueError:
			raise ValueError("Time string provided ({0}) does not have expected format ({1})".format(s[:19], pattern))
		except TypeError:
			raise TypeError("Time and pattern provided must be a string")

		return time_string

	# Parse method to be overridden by each command
	def parse(self, file_path, family_object):
		return


class Operator(BaseOperator):

	# Class Constructor
	def __init__(self, operationParams, baseObject={}):
		BaseOperator.__init__(self, operationParams, baseObject=baseObject)

		# Available commands list and filenames
		self._available_commands = dict()

		# Load the available commands according to the modules found in the package
		self.import_available_commands()

	def import_available_commands(self):

		# Import all the modules defined in the MODULES package
		for importer, modname, ispkg in pkgutil.walk_packages(path=MODULES.__path__, prefix=MODULES.__name__ + '.'):
			self._available_commands[modname]= dict()
			# self._available_commands[modname]["module"] = __import__(modname, fromlist=[modname])
			module = __import__(modname, fromlist=[modname])
			self._available_commands[modname]["class"] = module.Command()

		return

	def process(self, familyObj=FamilyObject(), baseObject={}):

		# Get the files to parse
		files_to_process = familyObj.getFiles()

		logger.debug("Entering Oi Commands files parser manager")

		for file_path in files_to_process:
			familyObj.clearDocuments()

			# Get file's name to find the unitID
			familyObj.fileName = os.path.basename(file_path)
			filePath = ''
			removeFile = False

			try:
				#Open file for writing
				if file_path.endswith(".tar.gz"):
					removeFile = True
					#Create a hidden, temporary file name without the .gz extension
					fileDir = os.path.dirname(file_path)
					tmp = os.path.basename(file_path).replace('.tar.gz', '.txt')
					filePath = os.path.join(fileDir, tmp)

					tar = tarfile.open(file_path, "r:gz")
					tar.extract(tmp, fileDir)
					tar.close()


					if os.path.exists(filePath)==True:
						if os.path.getsize(filePath) == 0:
					#		os.remove(filePath)
							raise IOError("")
					else:
						logger.warning("Could not create a hidden file \"{}\" in read mode: ".format(file_path))
						return
			except IOError:
				logger.warning("Could not open sample file \"{}\" in read mode: ".format(file_path), __file__)
				return

			if filePath == '':
				filePath = file_path

			f = open(filePath)
			lines = f.readlines()
			f.close()

			while lines != []:
				line = lines.pop(0).strip('\n|\r|\t')
				#validar linha
				if line == 'MML Command:':
					line = lines.pop(0).strip('\n|\r|\t')
					for command in self._available_commands:
						# To simplify invocation
						command = self._available_commands[command]["class"]
						if command.command_name_regex.match(line) is not None:
							try:
								for document in command.parse(file_path, lines, line):
									familyObj.setUnitID(command.command_name)
									try:
										data_time = familyObj.parseEnvelopeDataTime(document["DATETIME"])
									except ValueError as e:
										logger.warning("Could not build mediationEnvelope due to {0}: ".format(e), __file__)
										continue

									familyObj.addDocument({"dataTime": data_time, "granularitySec": 1440, "data": document})

									# Final operations to the fields with timestamp and granularity period
									self.nextOp(familyObj=familyObj, baseObject=baseObject)
									familyObj.clearDocuments()
							except (ValueError, TypeError, IOError) as e:
								logger.error(e)

							break

			if removeFile:
				os.remove(filePath)
