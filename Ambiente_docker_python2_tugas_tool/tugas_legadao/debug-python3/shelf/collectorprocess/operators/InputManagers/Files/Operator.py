#!/usr/bin/env python

__doc__ = \
    '''

'''

__version__ = '0.1'

__authors__ = [
    "Version 0.1: Francisco Santiago <francisco-j-santiago@telecom.pt>"
    "Version 1.0: Joao Pio <joao-t-pio@alticelabs.com>"
]

import importlib

InputManager = importlib.import_module("shelf.collectorprocess.operators.InputManagers.InputManager").InputManager
FamilyObject = importlib.import_module("shelf.collectorprocess.operators.FamilyObject").FamilyObject
tools = importlib.import_module("shelf.collectorprocess.operators.tools")
logger = importlib.import_module("shelf.collectorprocess.logger").logger


class Operator(InputManager):

    # Class Constructor
    def __init__(self, operationParams, baseObject={}):
        InputManager.__init__(self, operationParams, baseObject=baseObject)

        self.options_to_dict()
        self._file_patterns = list()
        self.load_file_patterns()

        # If path for getting files was provided as an argument, use that one instead
        if baseObject.args.input and baseObject.args.input != ".":
            self.options["path"] = baseObject.args.input

    def options_to_dict(self):
        """
        Converts XML options to simple python objects to allow serialization
        """
        if type(self.options["operationSpec"]) is not list:
            patterns = list()
            for pattern in self.options["operationSpec"]:
                patterns.append(pattern.text.strip())

            self.options["operationSpec"] = patterns

    def get_file_patterns(self):
        return self._file_patterns

    def set_file_patterns(self, file_patterns):
        self._file_patterns = file_patterns

    def load_file_patterns(self):

        for pattern in self.options["operationSpec"]:
            self._file_patterns.append(pattern)

    def process(self, familyObj=FamilyObject(), baseObject={}):

        familyObject = FamilyObject()
        familyObject.files = familyObj.files

        # If some previous operation did not fetch the file names yet
        if not familyObject.files:
            file_paths = tools.getFiles(self.options["path"], self._file_patterns)

            logger.debug("Gathered {0} files to process...".format(str(len(file_paths))), __file__)

            if len(file_paths) == 0:
                logger.warning("Found no files to process. Check patterns.".format(str(len(file_paths))), __file__)

            familyObject.setFiles(file_paths)

        # Set results for presentation
        baseObject.results.addResult(label="TOTAL FILES", value=len(familyObject.files))

        self.nextOp(familyObj=familyObject, baseObject=baseObject)
