#!/usr/bin/env python

__doc__ = \
    '''
    Operator that interprets the operations catalog that refers to the invoked operation.
    This class loads all custom operators available in "CustomOperators" and, when a new document arrives, each
    field's name is checked against the

'''

__version__ = '1.0'

__authors__ = [
    "Version 1.0: Joao Pio <joao-t-pio@telecom.pt>"
]

# Native libraries
import importlib
import pkgutil
import os
import xml.etree.cElementTree as ET

# Local libraries
import CustomOperators

BaseOperator = importlib.import_module("shelf.collectorprocess.operators.BaseOperator").BaseOperator
FamilyObject = importlib.import_module("shelf.collectorprocess.operators.FamilyObject").FamilyObject
logger = importlib.import_module("shelf.collectorprocess.logger").logger
tools = importlib.import_module("shelf.collectorprocess.operators").tools


# Exception declaration for when a Custom Operation mentioned in a catalog is not available
class OperationNotFoundError(Exception):
    pass


class Operator(BaseOperator):

    # Class Constructor
    def __init__(self, operationParams, baseObject={}):
        BaseOperator.__init__(self, operationParams, baseObject=baseObject)

        self._customOperators = dict()
        self.loadCustomOperators()

        self._operationsIndex = dict()
        self.buildOperationsIndex(baseObject=baseObject)

        self.convertCatalogOptions()

    @property
    def customOperators(self):
        return self._customOperators

    @customOperators.setter
    def customOperators(self, value):
        self._customOperators = value

    @property
    def operationsIndex(self):
        return self._operationsIndex

    @operationsIndex.setter
    def operationsIndex(self, value):
        self._operationsIndex = value

    def process(self, familyObj=FamilyObject(), baseObject={}):
        # Fetch the corresponding unit from index
        logger.debug("[CatalogOperators] Applying operations to document...")

        if familyObj.getUnitID() in self.operationsIndex:
            unit_obj = self.operationsIndex[familyObj.getUnitID()]

            # Iterates every document present in the family object
            for document in familyObj.getDocuments():
                # Iterates the items of the current unit that have operations associated
                for item in unit_obj["items"]:

                    item_from_index_id = item["itemID"]
                    operations = item["operations"]

                    if item_from_index_id in document["data"]:
                        for operation in operations:
                            if operation["type"] not in self.customOperators:
                                raise OperationNotFoundError(
                                    "Operation '{0}' not available. ".format(operation["type"]))
                            else:
                                info = dict()
                                info["itemID"] = item_from_index_id
                                info["document"] = document["data"]
                                info["operation"] = operation["operation"]
                                info["unitID"] = familyObj.getUnitID()

                                # Call the operator, passing the document to be operated on and the XML details of the operation
                                self.customOperators[operation["type"]].process(info, baseObject=baseObject)

            new_family_objs = familyObj

            # If there are operations related to the unit, but not specific items
            if unit_obj["operations"]:
                # Iterate operations
                for operation in unit_obj["operations"]:
                    # Check if operation exists in CustomOperators
                    if operation["type"] not in self.customOperators:
                        raise OperationNotFoundError("Operation '{0}' not available. ".format(operation["type"]))
                    else:

                        # Build 'info' object with information for the operation
                        info = dict()
                        info["familyObj"] = new_family_objs
                        info["operation"] = operation["operation"]

                        # Invoke operation's process, passing it the 'info' object. The method should return a familyObj, or a list of familyObjects
                        new_family_objs = self.customOperators[operation["type"]].process(info, baseObject=baseObject)

            # If several objects were returned
            if type(new_family_objs) is list:
                for famObj in new_family_objs:
                    self.nextOp(familyObj=famObj, baseObject=baseObject)
            # If only one familyObject was returned
            else:
                self.nextOp(familyObj=new_family_objs, baseObject=baseObject)
        else:
            self.nextOp(familyObj=familyObj, baseObject=baseObject)

    def loadCustomOperators(self):

        for importer, packageName, _ in pkgutil.iter_modules(CustomOperators.__path__):
            module = importer.find_module(packageName).load_module(packageName)
            self.customOperators[packageName] = module  # {"process": module.process, "readOptions": module.readOptions}

    def convertCatalogOptions(self):
        return

    def buildOperationsIndex(self, baseObject={}):

        """
        Builds an index of units and items with the corresponding operations, based on a provided catalog, with the following structure:

        index = {
        "unit1": {
        "operations": [ EntityCheck ],
        "items": [
        {
            "itemID": "item1"
            "operations": [ ApplyRegex ]
        },
        {
            "itemID": "item7"
            "operations":[ DictionaryReplace ]
        }
        ]
        },
        "unit2": {
        "operations": [ EntityCheck ],
        "items": [
        {
            "itemID": "item1"
            "operations": [ ApplyRegex ]
        },
        {
            "itemID": "item7"
            "operations":[ DictionaryReplace ]
        }
        ]
        }
}

"""

        root = self.getCatalogFromFile(baseObject=baseObject)

        for unit in root.findall("unit"):
            unit_id = unit.attrib["id"].upper()

            self.operationsIndex[unit_id] = {
                "items": list(),
                "operations": list()
            }

            for operation in unit.findall("operation"):

                if "complexoperation" not in operation.attrib or operation.attrib["complexoperation"] == "false":

                    operation_type = operation.attrib["type"]
                    if operation_type not in self.customOperators:
                        raise OperationNotFoundError("Operation '{0}' not available. ".format(operation_type))
                    else:

                        if hasattr(self.customOperators[operation_type], "readOptions"):
                            operation = self.customOperators[operation_type].readOptions(operation)

                        self.operationsIndex[unit_id]["operations"].append({
                            "type": operation_type,
                            "operation": operation  # self.customOperators[operationType]["readOptions"](operation)
                        })

            for item in unit.findall("item"):
                item_id = item.attrib["id"].upper()

                newItem = {
                    "itemID": item_id,
                    "operations": list()
                }

                for operation in item.findall("operation"):
                    if "complexoperation" not in operation.attrib or operation.attrib["complexoperation"] == "false":
                        operation_type = operation.attrib["type"]
                        if operation_type not in self.customOperators:
                            raise OperationNotFoundError("Operation '{0}' not available. ".format(operation_type))
                        else:

                            if hasattr(self.customOperators[operation_type], "readOptions"):
                                operation = self.customOperators[operation_type].readOptions(operation)

                            newItem["operations"].append({
                                "type": operation_type,
                                "operation": operation  # self.customOperators[operationType]["readOptions"](operation)
                            })

                self.operationsIndex[unit_id]["items"].append(newItem)

    def getCatalogFromFile(self, baseObject={}):

        """
        Loads the catalog from file to an ElementTree object
        """

        # check if catalog path is absolute
        if os.path.isfile(self.options["catalog"]):
            file_path = self.options["catalog"]
        # or else search in the catalogs folder
        else:
            try:
                file_path = tools.getFiles(baseObject.absFolders["catalogs"], self.options["catalog"]).pop(0)
            except IndexError:
                raise BaseOperator.OperationError(
                    "Could not find xml catalog with provided name '{0}' in folder '{1}'".format(
                        self.options["catalog"], baseObject.absFolders["catalogs"]))

        context = ET.iterparse(file_path, events=("start", "end"))
        root = None

        for event, elem in context:
            if event == "start" and root is None:
                root = elem

        return root
