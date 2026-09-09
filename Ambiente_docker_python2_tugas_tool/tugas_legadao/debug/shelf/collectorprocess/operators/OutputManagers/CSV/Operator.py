#!/usr/bin/env python

__version__ = '1.0'

__authors__ = [
    "Version 1.0: Joao Pio <joao-t-pio@telecom.pt>"
]

import xml.etree.cElementTree as ET
from datetime import datetime
import os
import codecs
import importlib

# Local libraries
BaseOperator = importlib.import_module("shelf.collectorprocess.operators.BaseOperator").BaseOperator
FamilyObject = importlib.import_module("shelf.collectorprocess.operators.FamilyObject").FamilyObject
logger = importlib.import_module("shelf.collectorprocess.logger").logger
tools = importlib.import_module("shelf.collectorprocess.operators.tools")


class Operator(BaseOperator):

    # Class Constructor
    def __init__(self, operationParams, baseObject={}):
        BaseOperator.__init__(self, operationParams, baseObject=baseObject)

        self.cont = 0

        self.pid = os.getpid()
        self.now = datetime.now().strftime("%Y%m%d%H%M%S")
        # If path for getting files was provided as an argument, use that one instead
        if baseObject.args.out and baseObject.args.out != ".":
            self.options["path"] = baseObject.args.out

        self.fileDirectory = self.options["path"]

        try:
            self.fileDirectory = self.options["path"]
        except KeyError:
            raise self.OperationError(
                "A path must be provided for csv output files either on spec file, or via commandline")

        if not os.path.isdir(self.fileDirectory):
            raise self.OperationError("Provided directory '{0}' does not exist.".format(self.fileDirectory))

        self.fileBaseName = "{0}_{1}_{2}_".format(self.getTaskName(), self.now, self.pid)
        self.filesByUnit = dict()

        self.unitsIndex = self.buildUnitsIndex(baseObject=baseObject)

        self._totalWrittenLines = 0
        self._totalWrittenFiles = 0

        self._unmappedItems = dict()
        self._unmappedUnits = dict()

        if "linecachesize" not in self.options:
            self.options["linecachesize"] = 100
        else:
            self.options["linecachesize"] = int(self.options["linecachesize"])

    def getFileBaseName(self):
        return self.fileBaseName

    def setFileBaseName(self, fileBaseName):
        self.fileBaseName = fileBaseName

    def getOutputDirectory(self):
        return self.fileDirectory

    def setOutputDirectory(self, fileDirectory):
        self.fileDirectory = fileDirectory

    def getFilesByUnit(self):
        return self.filesByUnit

    def setFilesByUnit(self, filesByUnit):
        self.filesByUnit = filesByUnit

    def getUnitsIndex(self):
        return self.unitsIndex

    def setUnitsIndex(self, unitsIndex):
        self.unitsIndex = unitsIndex

    def getTotalWrittenLines(self):
        return self.totalWrittenLines

    def setTotalWrittenLines(self, totalWrittenLines):
        self.totalWrittenLines = totalWrittenLines

    def incTotalWrittenLines(self):
        self.totalWrittenLines += 1

    def getUnmappedItems(self):
        return self.unmappedItems

    def setUnmappedItems(self, unmappedItems):
        self.unmappedItems = unmappedItems

    @property
    def totalWrittenLines(self):
        return self._totalWrittenLines

    @totalWrittenLines.setter
    def totalWrittenLines(self, value):
        self._totalWrittenLines = value

    @property
    def totalWrittenFiles(self):
        return self._totalWrittenFiles

    @totalWrittenFiles.setter
    def totalWrittenFiles(self, value):
        self._totalWrittenFiles = value

    @property
    def unmappedItems(self):
        return self._unmappedItems

    @unmappedItems.setter
    def unmappedItems(self, value):
        self._unmappedItems = value

    @property
    def unmappedUnits(self):
        return self._unmappedUnits

    @unmappedUnits.setter
    def unmappedUnits(self, value):
        self._unmappedUnits = value

    def oracleTypeToSQLType(self, value):
        if "NUMBER(" in value[:7]:
            value = "NUMERIC"
        elif "VARCHAR(" in value[:8] or "VARCHAR2(" in value[:9]:
            value = "VARCHAR"
        elif "NUMBER" == value:
            value = "FLOAT"
        elif "TIMESTAMP(" in value[:10]:
            value = "TIMESTAMP"
        elif "NUMBER(1)" == value:
            value = "BIT"

        return value

    def getCatalogFromFile(self, baseObject={}):

        """
        Loads the catalog from file to an ElementTree object
        """

        file_path = ""

        # check if catalog path is absolute
        if os.path.isfile(self.options["catalog"]):
            file_path = self.options["catalog"]
        # or else search in the catalogs folder
        else:
            try:
                file_path = tools.getFiles(baseObject.absFolders["catalogs"], self.options["catalog"]).pop(0)
            except IndexError:
                raise BaseOperator.OperationError(
                    "Could not find xml catalog with provided name '{0}' in folder '{1}'".format(self.options["catalog"], baseObject.absFolders["catalogs"]))

        context = ET.iterparse(file_path, events=("start", "end"))
        root = None

        for event, elem in context:
            if event == "start" and root is None:
                root = elem

        return root

    def buildUnitsIndex(self, baseObject={}):

        """
            Builds an index of units and items with the corresponding operations, based on a provided catalog, with the following structure:

            index = {
                "unit1": {
                "tablename": "",
                "active": True,
                "filename": "",
                "items":{
                "item1": {
                "bdtype": "NUMBER,
                "bdcolname": "item1",
                "dbn0type": "MT"
                }
                    "item2": {
                            "bdtype": "NUMBER,
                            "bdcolname": "item2",
                            "dbn0type": "ID"
                        }
                    }
                }
            }

"""

        root = self.getCatalogFromFile(baseObject=baseObject)

        units_index = dict()

        for table in root.findall("table"):

            unit_id = table.attrib["id"].upper()

            units_index[unit_id] = {
                "items": dict(),
                "tablename": "",
                "active": True,
                "columns": list()
            }

            units_index[unit_id]["tablename"] = table.attrib["tableName"]

            if "active" in table.attrib:
                if table.attrib["active"].upper() == "FALSE":
                    units_index[unit_id]["active"] = False

            units_index[unit_id]["tableName"] = ""
            if "tableName" in table.attrib:
                if table.attrib["tableName"] != "":
                    units_index[unit_id]["tableName"] = table.attrib["tableName"]

            for column in table.findall("column"):

                columnID = column.attrib["id"].upper()

                if column.attrib["dbn0type"] != "ENRICH":
                    units_index[unit_id]["columns"].append(columnID)

                units_index[unit_id]["items"][columnID] = {
                    "bdcolname": column.attrib["bdcolname"],
                    "bdtype": column.attrib["bdtype"],
                    "dbn0type": column.attrib["dbn0type"]
                }

        return units_index

    def buildEnrichmentHeader(self, unitData, baseObject):

        # Build enrichment columns line
        enrichment_block_str = ""
        # Collections
        enrichment_block_str += "{0}\n".format(baseObject.vars["enrichment"]["SCOPE"])
        # Correlation key
        for corrKey in baseObject.vars["enrichment"]["CORRKEYS"]:
            enrichment_block_str += "{0};".format(corrKey)

        # Replace extra separator in the end of header2 by newline
        enrichment_block_str = "{0}\n".format(enrichment_block_str[:-1])

        for itemID in baseObject.vars["enrichment"]["FIELDS"]:
            itemInfo = unitData["items"][itemID]

            enrichment_block_str += "{0}|{1}|{2};".format(itemInfo["bdcolname"],
                                                          self.oracleTypeToSQLType(itemInfo["bdtype"]),
                                                          itemInfo["dbn0type"])

        # Replace extra separator in the end of header2 by newline
        enrichment_block_str = "{0}\n".format(enrichment_block_str[:-1])

        return enrichment_block_str

    # def open(self, fileName):

    def writeFileHeader(self, fileInfo, unitID, baseObject={}):
        units_index = self.getUnitsIndex()

        # fileInfo = self.getFileInfo(unitID)

        # Build the header1 line containing the table's name
        header1 = "{0}\n".format(units_index[unitID]["tablename"])

        # Build the header2 line containing the columns information
        header2 = ""

        for itemID in units_index[unitID]["columns"]:
            itemInfo = units_index[unitID]["items"][itemID]

            if itemInfo["dbn0type"].upper() == "ENRICH": continue

            header2 += "{0}|{1}|{2};".format(itemInfo["bdcolname"], self.oracleTypeToSQLType(itemInfo["bdtype"]),
                                             itemInfo["dbn0type"])

        # Replace extra separator in the end of header2 by newline
        header2 = "{0}\n".format(header2[:-1])

        # CHECK IF OPEN FILE WORKS
        try:
            f = codecs.open(fileInfo["filePath"], "w", "utf-8")

            # Write table name header to file
            f.write(header1)
            # Write column header to file
            f.write(header2)

            if "enrichment" in baseObject.vars:
                enrichment_header = self.buildEnrichmentHeader(units_index[unitID], baseObject)

                f.write(enrichment_header)

            # Write start data beginning
            f.write("START_DATA\n")

            f.close()

            fileInfo["file"] = codecs.open(fileInfo["filePath"], "a")
        except IOError, e:
            logger.warning("Could not open file due to {0}".format(e), __file__)
            return False

    def getFileInfo(self, unitID, baseObject={}):
        files_by_unit = self.getFilesByUnit()
        # self.cont=self.cont+1

        if "join" in self.options:
            join = self.options["join"]
        else:
            join = "true"

        if join == "false":
            self.cont = self.cont + 1
            self.fileBaseName = "{0}_{1}_{2}_{3}_".format(self.getTaskName(), datetime.now().strftime("%Y%m%d%H%M%S"),
                                                          self.pid, self.cont)

        if join == "false" or unitID not in files_by_unit:
            # Creates an entry with a fileName based on the unit ID
            files_by_unit[unitID] = dict()
            # If filename attribute was provided in catalog, use that
            if self.unitsIndex[unitID]["tableName"]:
                files_by_unit[unitID]["tableName"] = "{0}{1}.csv".format(self.getFileBaseName(),
                                                                         self.unitsIndex[unitID]["tableName"])
            else:
                # Any other way, use the unit's ID
                files_by_unit[unitID]["tableName"] = "{0}{1}.csv".format(self.getFileBaseName(), unitID)

            files_by_unit[unitID]["filePath"] = os.path.join(self.getOutputDirectory(),
                                                             files_by_unit[unitID]["tableName"])
            files_by_unit[unitID]["file"] = None
            files_by_unit[unitID]["outStream"] = ""
            files_by_unit[unitID]["linesInCache"] = 0

            # print filesByUnit[unitID]["filePath"]
            self.totalWrittenFiles += 1
            self.writeFileHeader(files_by_unit[unitID], unitID, baseObject=baseObject)

        return files_by_unit[unitID]

    def generateEmptyDocument(self, unitID):
        units_index = self.getUnitsIndex()
        # Generates an dictionary with all fields of a given table empty
        return dict([(x, "") for x in units_index[unitID]["columns"]])

    def writeOut(self, fileInfo):

        if fileInfo["linesInCache"] > self.options["linecachesize"]:

            f = None
            # CHECK IF OPEN FILE WORKS
            try:
                # f = codecs.open(fileInfo["filePath"], "a", "utf-8")
                f = fileInfo["file"]

                f.write(fileInfo["outStream"])

                fileInfo["outStream"] = ""
                fileInfo["linesInCache"] = 0

            # f.close()

            except IOError, e:
                logger.warning("Could not open file due to {0}".format(e), __file__)
                return False

    def process(self, familyObj=FamilyObject(), baseObject={}):

        logger.debug("Writing stuff to file...", __file__)
        units_index = self.getUnitsIndex()
        unit_id = familyObj.getUnitID()

        if unit_id not in units_index:
            if unit_id not in self.unmappedUnits:
                self.unmappedUnits[unit_id] = ""
                logger.warning("Unit '{0}' not mapped in client catalog, but found in document. ".format(unit_id),
                               __file__)
            self.nextOp(familyObj=familyObj, baseObject=baseObject)
            return

        # Ignore unit if not active
        if units_index[unit_id]["active"] is False:
            logger.warning("Unit '{0}' is not active due to administrative configuration.".format(unit_id), __file__)
            return

        if familyObj.documents:
            file_info = self.getFileInfo(unit_id, baseObject=baseObject)

            for document in familyObj.documents:
                content_line = ""

                # Create a document that contains all counters of current unit
                doc_out = self.generateEmptyDocument(unit_id)

                for itemID in document["data"].keys():

                    if itemID not in doc_out:

                        if unit_id not in self.unmappedUnits:
                            self.unmappedUnits[unit_id] = dict()
                        if itemID not in self.unmappedUnits[unit_id]:
                            logger.warning(
                                "Item '{0}' of unit '{1}' not mapped in client catalog, but found in document".format(
                                    itemID, unit_id), __file__)
                            self.unmappedUnits[unit_id][itemID] = ""

                doc_out.update(document["data"])

                for key in units_index[unit_id]["columns"]:

                    try:
                        content_line += "{0};".format(str(doc_out[key]).replace(";", ""))
                    # This controll prevents encoding errors from breaking the output. Unknown characters are discarded
                    except UnicodeDecodeError:
                        uValue = unicode(doc_out[key], errors='ignore')
                        content_line += "{0};".format(str(uValue).replace(";", ""))

                # Replace extra separator in the end of each row by newline
                content_line = "{0}\n".format(content_line[:-1])

                file_info["outStream"] += content_line

                file_info["linesInCache"] += 1

                self.totalWrittenLines += 1
                self.writeOut(file_info)

        self.nextOp(familyObj=familyObj, baseObject=baseObject)

    def finish(self, familyObj=None, baseObject={}):

        # Remove minimum limit for lines to be written out
        self.options["linecachesize"] = 0

        for unitID, fileInfo in self.getFilesByUnit().items():
            self.writeOut(fileInfo)

            self.totalWrittenLines += 1

            fileInfo["file"].close()

        # Set result values
        duration = datetime.now() - baseObject.results.startTime

        duration_in_seconds = duration.seconds + duration.microseconds / float(1000000)

        lines_written = self.getTotalWrittenLines()

        lines_per_sec = float("{0:.0f}".format(lines_written / duration_in_seconds))

        baseObject.results.addResult(label="TOTAL OUTPUT FILES", value=self.totalWrittenFiles)
        baseObject.results.addResult(label="TOTAL EVENTS", value=lines_written)

        # Main process does not process files
        if lines_written != 0:
            baseObject.results.addResult(label="OUTPUT FILES", value=self.totalWrittenFiles, pid=self.pid)
            baseObject.results.addResult(label="EVENTS", value=lines_written, pid=self.pid)
            baseObject.results.addResult(label="DURATION".format(self.pid), value=duration_in_seconds, pid=self.pid,
                                         unit="secs")
            baseObject.results.addResult(label="PERFORMANCE".format(self.pid), value=lines_per_sec, pid=self.pid,
                                         unit="lines/sec")
