#!/usr/bin/env python

__doc__ = '''
'''

__version__ = '0.1'

__authors__ = [
    "Version 0.1: Francisco Santiago <francisco-j-santiago@telecom.pt>"
]

# Native libraries
import os
import importlib
import xml.etree.cElementTree as ET

# Local libraries
FamilyObject = importlib.import_module("shelf.collectorprocess.operators.FamilyObject").FamilyObject
logger = importlib.import_module("shelf.collectorprocess.logger.logger")

class FlowManager():

    # Class Constructor
    def __init__(self, operation, baseObject={}):

        self.operationsQueue = list()
        self.operation = operation

        self.buildOperationsQueue(operation, baseObject=baseObject)

    def getOperation(self):
        return self.operation

    def setOperation(self, operation):
        self.operation = operation

    def getOperationsQueue(self):
        return self.operationsQueue

    def setOperationsQueue(self, operationsQueue):
        self.operationsQueue = operationsQueue

    def getFirstOperation(self):
        return self.getOperationsQueue()[0]

    def addOperationToQueue(self, operation):
        self.operationsQueue.append(operation)
        return True

    def buildOperationsQueue(self, operation, baseObject={}):
        """
            Gets an operation name.
            Builds the operation's full name to be recognized against the project's folder structure.
            Tries to load the operation
        """

        operation_instances = list()

        element = type(ET.Element(None))

        # Initialize all operations
        for operationName, operationID in baseObject.operationList:
            operation = self.loadOperationModule(operationName, baseObject=baseObject)

            operation_params = {
                "operationName": operationName,
                "operationID": operationID,
                "taskName": self.getOperation()
            }

            operation = operation.Operator(operation_params, baseObject=baseObject)

            # Clear XML options from baseObject and this object's options to allow serialization
            if isinstance(operation.options["operationSpec"], element):
                operation.options["operationSpec"] = {}

            operation_instances.append(operation)

        next_operation_index = 1
        n_operations = len(operation_instances)

        for operation in operation_instances:

            if next_operation_index < n_operations:
                operation.setNextOperation(operation_instances[next_operation_index])
            else:
                operation.lastOperation = True

            next_operation_index += 1

            self.addOperationToQueue(operation)

    def loadOperationModule(self, operation_name, baseObject={}):
        """
            Gets a source name like "Operators.{OPERATOR_TYPE}.{OPERATION_NAME}"
               Ex:"Operators.HUAWEI.HUAWEIPerformanceCSV"
            Loads the corresponding operation's module
        """

        # Remove python if mistakenly put in the operation's name
        if ".py" in operation_name[-3:]:
            operation_name = os.path.splitext(operation_name)[0]

        return importlib.import_module("shelf.collectorprocess.{0}".format(operation_name))

        # return __import__(operation_name, fromlist=["Operator"])

    def start(self, familyObj=FamilyObject(), baseObject={}):

        first_operation = self.getFirstOperation()
        first_operation.start(familyObj=familyObj, baseObject=baseObject)

        self.end(baseObject=baseObject)

        logger.debug("Finished processing all operations...", __file__)

        return True

    def end(self, baseObject={}):

        logger.debug("Calling finish...", __file__)
        # Calls the finish method on all operations from the first to the last
        for operation in self.getOperationsQueue():
            operation.end(baseObject=baseObject)
