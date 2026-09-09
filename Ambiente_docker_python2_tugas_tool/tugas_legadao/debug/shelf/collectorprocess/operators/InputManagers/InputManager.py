#!/usr/bin/env python

__doc__ = \
    '''

'''

__version__ = '0.1'

__authors__ = [
    "Version 0.1: Francisco Santiago <francisco-j-santiago@telecom.pt>"
]

# Native libraries
from datetime import datetime
import importlib

# Local libraries
BaseOperator = importlib.import_module("shelf.collectorprocess.operators.BaseOperator").BaseOperator
FamilyObject = importlib.import_module("shelf.collectorprocess.operators.FamilyObject").FamilyObject
logger = importlib.import_module("shelf.collectorprocess.logger").logger


class InputManager(BaseOperator):

    # Class Constructor
    def __init__(self, operationParams, baseObject={}):

        BaseOperator.__init__(self, operationParams, baseObject=baseObject)

        if "multi" in self.options:
            try:
                self.options["multi"] = int(self.options["multi"])
                if self.options["multi"] <= 0:
                    del self.options["multi"]
                else:
                    baseObject.multi = {
                        "nSubProcesses": self.options["multi"],
                        "familyObjects": list()
                    }
            except ValueError:
                del self.options["multi"]
                logger.warning("Option 'multi' must be an integer in '{0}'.".format(baseObject.operationSpecFilesName),
                               __file__)

    def start(self, familyObj=FamilyObject(), baseObject={}):
        """
        Someone invoked this operation to process a batch of lines
        """
        self.batchStartTime = datetime.now()

        # Get the next operation
        self.process(familyObj=familyObj, baseObject=baseObject)

    def nextOp(self, familyObj=FamilyObject(), baseObject={}):
        """
        This operation finished processing a batch of lines and is invoking the next operation
        """

        logger.debug("Preparing to call next operation in nextOp...", __file__)
        if not self.lastOperation:

            if self.benchMark is True:
                self.performBenchMark(familyObj=familyObj, baseObject=baseObject)

            if self.cache is True:

                if familyObj.unitID not in self.familyObjCache:
                    self.familyObjCache[familyObj.unitID] = FamilyObject()
                    self.familyObjCache[familyObj.unitID].unitID = familyObj.unitID
                    self.familyObjCache[familyObj.unitID].fileName = familyObj.fileName

                cached_family_object = self.familyObjCache[familyObj.unitID]

                for document in familyObj.documents:
                    cached_family_object.addDocument(document)
                    self.nDocsInCache += 1

                for source in familyObj.sources:
                    cached_family_object.addSource(source)
                    self.nDocsInCache += 1

                if self.nDocsInCache >= self.cacheSize:
                    for unitID, cacheFamilyObj in self.familyObjCache.items():

                        if "multi" not in self.options:
                            # Get the next operation
                            self.getNextOperation().start(familyObj=cacheFamilyObj, baseObject=baseObject)
                        else:
                            baseObject.multi["familyObjects"].append(cacheFamilyObj)

                        del self.familyObjCache[cacheFamilyObj.unitID]

                    self.resetCache()

            else:
                logger.debug("Sending familyObject to next operation...", __file__)
                if "multi" not in self.options:
                    # Get the next operation
                    self.getNextOperation().start(familyObj=familyObj, baseObject=baseObject)
                else:
                    baseObject.multi["familyObjects"].append(familyObj)

        else:
            logger.debug("Reached last operation...", __file__)

        logger.debug("Returning to operation...", __file__)
        return

    def finish(self, familyObj=None, baseObject={}):

        if "multi" in baseObject.operationsOptions[self.operationID]:
            del baseObject.operationsOptions[self.operationID]["multi"]
