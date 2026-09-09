#!/usr/bin/env python

__doc__ = \
	'''
	TELCORDIA Performance files parser manager
'''

__version__ = '1.0'

__authors__ = [
	"Version 1.0: Bruno Silva <bruno-e-silva@alticelabs.com>"
]

import os
import pkgutil
import time
import importlib

# Local libraries
BaseOperator = importlib.import_module("shelf.collectorprocess.operators.BaseOperator").BaseOperator
FamilyObject = importlib.import_module("shelf.collectorprocess.operators.FamilyObject").FamilyObject
MODULES = importlib.import_module("shelf.collectorprocess.operators.Readers.TELCORDIA.COMMANDS.MODULES")
logger = importlib.import_module("shelf.collectorprocess.logger").logger


# This class represents a command processor. Each command must extend this class
class Command(object):

	def __init__(self):

		self._command_name = None
		self._file_name_regex = None

	@property
	def file_name_regex(self):
		return self._file_name_regex

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
		familyObj.clearFiles()

		logger.debug("Entering TELCORDIA Commands files parser manager")

		for file_path in files_to_process:

			familyObj.clearDocuments()

			# Get file's name to find the unitID
			familyObj.fileName = os.path.basename(file_path)

			for command in self._available_commands:
				# To simplify invocation
				command = self._available_commands[command]["class"]
				if command.file_name_regex.match(familyObj.fileName) is not None:
					try:
						for document in command.parse(file_path):
							familyObj.addDocument(document)
							familyObj.setUnitID(command.command_name)
							self.nextOp(familyObj=familyObj, baseObject=baseObject)
							familyObj.clearDocuments()
					except (ValueError, TypeError, IOError) as e:
						logger.error(e)