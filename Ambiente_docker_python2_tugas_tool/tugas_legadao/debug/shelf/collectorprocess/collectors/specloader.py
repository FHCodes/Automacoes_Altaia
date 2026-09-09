#!/usr/bin/env python

__doc__ = '''
	Loads the spec file of tasks from xml to python data formats
'''

__version__ = '0.1'

__authors__ = [
				"Version 0.1: Francisco Santiago <francisco-j-santiago@telecom.pt>"
			]

import xml.etree.cElementTree as ET
import os
import importlib

# Local libraries
logger = importlib.import_module("shelf.collectorprocess.logger").logger

# Exception declaration for an invalid spec file
class InvalidSpecError(Exception): pass


def loadOperationSpec(operation="", instance="", scope="", baseObject={}):

	spec = None

	spec_to_use = ""
	if scope: spec_to_use = scope
	elif instance: spec_to_use = instance

	if spec_to_use:
		spec_path = os.path.join(baseObject.absFolders["colls"], operation, spec_to_use, baseObject.operationSpecFilesName)

		try:
			spec = ET.parse(spec_path)
		except IOError:
			logger.warning("Could not find the specified '{0}' file '{1}'".format(baseObject.operationSpecFilesName, spec_path), __file__)
			spec_path = ""
			spec = None

	if spec is None:
		spec_path = os.path.join(baseObject.absFolders["colls"], operation, baseObject.operationSpecFilesName)

		try:
			spec = ET.parse(spec_path)
		except IOError:
			logger.error("Could not find the specified '{0}' file '{1}'".format(baseObject.operationSpecFilesName, spec_path), __file__)
			return False

	spec = spec.getroot()

	operations = dict()
	operations_options = dict()
	operation_list = list()

	spec_attrs = spec.attrib

	index = 0

	# Build operation name and load it
	for node in spec.findall("operation"):

		options = dict(node.attrib.items())

		operation_type = options.get("type")

		if operation_type is None:
			raise InvalidSpecError("Attribute 'type' is required for <operation> nodes. Not found in spec file '{1}'".format(baseObject.operationSpecFilesName, operation + "." + spec_to_use))

		operation_name = "{0}.{1}".format(baseObject.folders["operators"], operation_type)

		operation_id = "{0}.{1}.{2}".format(baseObject.folders["operators"], operation_type, index)

		if "name" in options:
			operation_name += ".{0}".format(options["name"])
			operation_id += ".{0}".format(options["name"])

		operation_name += ".{0}".format(baseObject.operationBaseName)
		operation_id += ".{0}".format(baseObject.operationBaseName)

		# Makes the whole XML node available in case the operation needs to access some unknown extra information
		options["operationSpec"] = node
		options["instance"] = instance

		options.update(spec_attrs)

		operations[operation_name] = options
		operations_options[operation_id] = options
		operation_list.append((operation_name, operation_id))

		index += 1

	if len(operation_list) == 0:
		raise InvalidSpecError("No operations found in the provided {0} file '{1}'".format(baseObject.operationSpecFilesName, operation + "." + spec_to_use))

	baseObject.operations = operations
	baseObject.operationsOptions = operations_options
	baseObject.operationList = operation_list
