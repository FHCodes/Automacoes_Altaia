#!/usr/bin/env python

__doc__ = '''

'''

__version__ = '0.1'

__authors__ = ["Version 0.1: Francisco Santiago <francisco-j-santiago@telecom.pt>"]

# Native libraries
import abc
import importlib

# Local libraries
logger = importlib.import_module("shelf.collectorprocess.logger").logger
FamilyObject = importlib.import_module("shelf.collectorprocess.operators.FamilyObject").FamilyObject


class BaseOperator(object):

    # Exception declaration for when an operator cannot be created for some reason
    class OperationError(Exception):
        pass

    # Class Constructor
    def __init__(self, operationParams, baseObject={}):

        # The operation identifies itself using this name
        self.operationName = operationParams["operationName"]
        self.operationID = operationParams["operationID"]
        self._options = baseObject.operationsOptions[self.operationID]
        self.operatorName = self.getOptions()["type"]
        self._baseObject = baseObject

        self._lastOperation = False

        if "lastop" in operationParams:
            self.lastOperation = True

        # The name of the task that initiated this flow
        self.taskName = operationParams["taskName"]

        self.nextOperation = None

        """ Cache related properties """
        self._cache = False
        self._cacheSize = 0

        if "cache" in self.options:
            self._cacheSize = int(self.options["cache"])
            self._cache = True

        self._nDocsInCache = 0
        self._familyObjCache = dict()

        """ BenchMark related properties """
        # For benchmarking. This is a list of integers representing the speed (lines/sec) processed only by this operation
        self._benchMark = False

        if "benchmark" in self.getOptions() and self.options["benchmark"] == "true":
            self._benchMark = True

    @property
    def operatorName(self): return self._operatorName
    @operatorName.setter
    def operatorName(self, value): self._operatorName = value
    @property
    def lastOperation(self): return self._lastOperation
    @lastOperation.setter
    def lastOperation(self, value): self._lastOperation = value
    @property
    def options(self): return self._options
    @options.setter
    def options(self, value): self._options = value
    @property
    def benchMark(self): return self._benchMark
    @benchMark.setter
    def benchMark(self, value): self._benchMark = value
    @property
    def cache(self): return self._cache
    @cache.setter
    def cache(self, value): self._cache = value
    @property
    def nDocsInCache(self): return self._nDocsInCache
    @nDocsInCache.setter
    def nDocsInCache(self, value): self._nDocsInCache = value
    @property
    def cacheSize(self): return self._cacheSize
    @cacheSize.setter
    def cacheSize(self, value): self._cacheSize = value
    @property
    def familyObjCache(self): return self._familyObjCache
    @familyObjCache.setter
    def familyObjCache(self, value): self._familyObjCache = value
    @property
    def baseObject(self): return self._baseObject
    @baseObject.setter
    def baseObject(self, value): self._baseObject = value

    def getOperationName(self): return self.operationName
    def setOperationName(self, operationName): self.operationName = operationName
    def getOptions(self): return self._options
    def setOptions(self, options): self._options = options
    def getTaskName(self): return self.taskName
    def setTaskName(self, taskName): self.taskName = taskName

    def resetCache(self):
        self.familyObjCache = dict()
        self.nDocsInCache = 0

    def getNextOperation(self):
        #Return the next operation's instance
        return self.nextOperation

    def setNextOperation(self, nextOperation):
        #Return the next operation's instance
        self.nextOperation = nextOperation

    def start(self, familyObj=FamilyObject(), baseObject={}):
        """
            Someone invoked this operation to process a batch of lines
        """

        #Get the next operation
        self.process(familyObj=familyObj, baseObject=baseObject)

    def nextOp(self, familyObj=FamilyObject(), baseObject={}):
        """
            This operation finished processing a batch of lines and is invoking the next operation
        """

        logger.debug("Preparing to call next operation in nextOp...", __file__)
        if not self.lastOperation:

            if self.cache is True:

                if familyObj.unitID not in self.familyObjCache:
                    self.familyObjCache[familyObj.unitID] = FamilyObject()
                    self.familyObjCache[familyObj.unitID].unitID = familyObj.unitID
                    self.familyObjCache[familyObj.unitID].fileName = familyObj.fileName

                cachedFamilyObject = self.familyObjCache[familyObj.unitID]

                for document in familyObj.documents:
                    cachedFamilyObject.addDocument(document)
                    self.nDocsInCache += 1

                if self.nDocsInCache >= self.cacheSize:
                    for unitID, cacheFamilyObj in self.familyObjCache.items():
                        # Get the next operation
                        self.getNextOperation().start(familyObj=cacheFamilyObj, baseObject=self.baseObject)

                        del self.familyObjCache[cacheFamilyObj.unitID]

                    self.resetCache()

            else:
                logger.debug("Sending familyObject to next operation...", __file__)
                # Get the next operation
                self.getNextOperation().start(familyObj=familyObj, baseObject=self.baseObject)
        else:
            logger.debug("Reached last operation...", __file__)
        logger.debug("Returning to operation...", __file__)
        return

    def end(self, familyObj=FamilyObject(), baseObject={}):
        """
            Will be called when the FlowManager determines the operation flow is over.
        """

        logger.debug("Dealing with docs in cache to finish...", __file__)
        if self.cache is True:
            for unitID, cacheFamilyObj in self.familyObjCache.items():
                #Get the next operation
                self.getNextOperation().start(familyObj=cacheFamilyObj, baseObject=self.baseObject)

                del self.familyObjCache[cacheFamilyObj.unitID]

            self.resetCache()

        self.finish(familyObj=familyObj, baseObject=baseObject)

    def finish(self, familyObj=None, baseObject={}):
        """
            To be defined in each of the operator if desired.
            Will be called when the operation flow is over.
        """
        return

    @abc.abstractmethod
    def process(self, familyObj={}, baseObject={}):
        pass
