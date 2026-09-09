#!/usr/bin/env python

__doc__ = \
    '''
    Parser for HUAWEI SRAN Parameters CMExport XML

    Spec file syntax:
    <operation type="Readers" name="HUAWEI.XML.CMEXPORT" enrich="HUAWEI_OSS_RAN_CM.SRAN" />
'''

__version__ = '1.0'

__authors__ = [
    "Version 1.0: Marco Jeronimo <marco-a-jeronimo@alticelabs.com>"
]

import copy
import os
import re
from datetime import datetime
import importlib
import json
from lxml import etree
import gzip
import io
from collections import OrderedDict

# Local libraries
BaseOperator = importlib.import_module("shelf.collectorprocess.operators.BaseOperator").BaseOperator
FamilyObject = importlib.import_module("shelf.collectorprocess.operators.FamilyObject").FamilyObject
logger = importlib.import_module("shelf.collectorprocess.logger").logger
mongoCon = importlib.import_module(
    "shelf.collectorprocess.operators.OutputManagers.Mongo.Operator").mongoConnection


class Operator(BaseOperator):
    def __init__(self, operationParams, baseObject={}):
        BaseOperator.__init__(self, operationParams, baseObject=baseObject)

        config = json.load(open('/opt/alticelabs/namf/src/shelf/collectorprocess/config/mongo_enrich_config.json'))
        config.update(
            json.load(open('{0}/{1}/config.json'.format(config['location'], self.options['enrich'].replace('.', '/'))), object_pairs_hook=OrderedDict))
        # Get absolute path of directory where script is locate
        dir_of_script = os.path.dirname(os.path.abspath(__file__))
        self._enrichMapping = json.load(open('{0}/mongoEnrichMapping.json'.format(dir_of_script)), object_pairs_hook=OrderedDict)
        self._modelsMapping = json.load(open('{0}/modelsMapping.json'.format(dir_of_script)))
        self._mongoConnection = mongoCon(config)
        self._mongoConnection.getConnection()
        self._MNC_directory = {'16': 'Oi', '24': 'Oi', '30': 'Oi', '31': 'Oi', '01': 'Vivo', '1': 'Vivo', '06': 'Vivo',
                               '6': 'Vivo', '10': 'Vivo', '11': 'Vivo', '23': 'Vivo', '02': 'TIM', '2': 'TIM',
                               '03': 'TIM', '3': 'TIM', '04': 'TIM', '4': 'TIM', '08': 'TIM', '8': 'TIM', '99': 'FAKE'}

    def process(self, familyObj=FamilyObject(), baseObject={}):
        logger.debug("[Reader] Reading HUAWEI Parameters CMExport XML files' contents...")

        # Get the files to parse
        files_to_process = familyObj.getFiles()

        for file_path in files_to_process:
            try:
                # Just for semantic reasons, in case a human reads a log containing the path
                file_path = os.path.abspath(file_path)

                # Get file's name
                fileName = os.path.basename(file_path)
                dateTime, elementName, ip = self.getFilenameInfo(fileName)

                if dateTime is None or elementName is None or ip is None:
                    continue

                familyObj.clearDocuments()
                familyObj.fileName = fileName

                try:
                    if file_path.endswith('.gz'):
                        elementNameNe, prefixNe, typeNe = self.getElementNe(gzip.open(file_path))
                        listMoDuplicated = self.getDuplicateElement(gzip.open(file_path), prefixNe, typeNe)
                        enrichDict, mappingKeys = self.getNetworkMap(gzip.open(file_path), prefixNe)
                        self.processFile(gzip.open(file_path), familyObj, baseObject, elementNameNe, prefixNe, typeNe,
                                         enrichDict, mappingKeys, listMoDuplicated)
                    else:
                        elementNameNe, prefixNe, typeNe = self.getElementNe(file_path)
                        listMoDuplicated = self.getDuplicateElement(file_path, prefixNe, typeNe)
                        enrichDict, mappingKeys = self.getNetworkMap(file_path, prefixNe)
                        self.processFile(file_path, familyObj, baseObject, elementNameNe, prefixNe, typeNe, enrichDict,
                                         mappingKeys, listMoDuplicated)

                except etree.ParseError:
                    logger.warning("Malformed Huawei XML file '{0}'".format(fileName))
            except IOError:
                logger.warning("Could not open sample file \"{}\" in read mode: ".format(file_path), __file__)

    # Gets the datetime, elementName and ip from the filename
    def getFilenameInfo(self, fileName):
        date = None
        elementName = None
        ip = None

        match = re.match(r'CMExport_(?P<elementName>.+?)_(?P<ip>[^_]+)_(?P<dateTime>\d{10})\.xml.*', fileName)

        if match:
            dateTime = match.group("dateTime")
            elementName = match.group("elementName")
            ip = match.group("ip")
            try:
                dateTimeObject = datetime.strptime(dateTime, "%Y%m%d%H").date()
                date = dateTimeObject.strftime('%Y-%m-%d %H:00:00')
            except Exception as e:
                logger.warning(
                    "Filename \"%s\" does not have the expected format \"CMExport_(?P<elementName>.+?)_(?P<ip>[^_]+)_("
                    "?P<dateTime>\\d{10})\\.xml\"" % fileName)
        else:
            logger.warning(
                "Filename \"%s\" does not have the expected format \"CMExport_(?P<elementName>.+?)_(?P<ip>[^_]+)_("
                "?P<dateTime>\\d{10})\\.xml\"" % fileName)

        return date, elementName, ip

    def getElements(self, filename, tag):
        context = iter(etree.iterparse(filename, events=('start', 'end')))
        # Get root element
        _, root = next(context)
        namespace = None
        for event, elem in context:
            if event == 'start' and namespace is None:
                if "}" in elem.tag:
                    namespace = elem.tag.split("}")[0].strip("{")
                    namespace = "{" + namespace + "}"
                else:
                    namespace = ""
            if event == 'end' and elem.tag == namespace + tag:
                yield elem, namespace
                elem.clear()
        root.clear()

    def getPrefixNE(self, className):
        prefixNe = None
        neRegex = "^(?P<PREFIX>.+)NE$"
        neMatch = re.match(neRegex, className)
        if neMatch:
            prefixNe = neMatch.group("PREFIX")
        return prefixNe

    def getElementNe(self, filename):
        elementName = None
        prefixNe = None
        typeNe = None
        firstMO = True
        try:
            context = iter(etree.iterparse(filename, events=('start', 'end')))
            _, root = next(context)
        except etree.ParseError as e:
            logger.warning("Malformed HUAWEI Parameter GExport XML file '{0}'".format(filename))
            return e

        for event, elem in context:
            if event == 'start' and elem.tag == "MO" and firstMO:
                firstMO = False
                # Get the PREFIX from the NE class - Should only happen once every file and in the case of "getElements"
                prefixNe = self.getPrefixNE(elem.attrib["className"].upper())
                # Success extracting prefixNe
                if prefixNe:
                    newDocument = dict()
                    # Process all child attributes
                    self.processMOAttr(elem, newDocument)
                    # Get elementName from name field, used in all other families of the file
                    elementName = newDocument["NAME"].upper()
                    typeNe = newDocument["NETYPE"]
                    elem.clear()
                    break
        root.clear()
        del context
        return elementName, prefixNe, typeNe

    def getDuplicateElement(self, filename, prefixNe, typeNe):
        listMoDuplicated = list()
        tempListMos = list()
        try:
            context = iter(etree.iterparse(filename, events=('start', 'end')))
            _, root = next(context)
        except etree.ParseError as e:
            logger.warning("Malformed HUAWEI Parameter GExport XML file '{0}'".format(filename))
            return e

        for event, elem in context:
            if event == 'start' and elem.tag == "MO":
                className = elem.attrib["className"].upper().replace(prefixNe.upper(), "")
                if typeNe in self._modelsMapping.keys() and className in self._modelsMapping[
                    typeNe].keys():
                    className = self._modelsMapping[typeNe][className]
                idMo = className + '_' + elem.attrib["fdn"].upper()
                if idMo not in tempListMos:
                    tempListMos.append(idMo)
                else:
                    listMoDuplicated.append(idMo)
                elem.clear()

        root.clear()
        del context
        return listMoDuplicated

    def processMOAttr(self, managedObject, newDocument):
        # Iterate all children to retrieve their keys and values to add to the document
        for child in managedObject.findall("*"):
            if child.tag == "attr":
                if child.text is not None:
                    child.text = child.text.strip()
                else:
                    child.text = ""
                newDocument[child.attrib["name"].upper()] = child.text

        return True

    def getNetworkMap(self, filename, prefixNe):
        enrichmentData = dict()
        mappingKeys = dict()
        unitsToGet = {"BTS": [{"BTSID": ["BTSNAME"]}], "RNCBASIC": [{"LOGICRNCID": ["RNCNAME"]}],
                      "URNCBASIC": [{"LOGICRNCID": ["RNCNAME"]}],
                      "GCELL": [{"NRCELLID": ["CELLNAME"]}, {"CELLID": ["CELLNAME", "BTSID"]},
                                {"ULOCELLID": ["CELLNAME"]}, {"LOCELL": ["CELLNAME"]}, {"LOCALCELLID": ["CELLNAME"]}],
                      "UCELL": [{"NRCELLID": ["CELLNAME"]}, {"CELLID": ["CELLNAME"]}, {"ULOCELLID": ["CELLNAME"]},
                                {"LOCELL": ["CELLNAME"]}, {"LOCALCELLID": ["CELLNAME"]},
                                {"NRCELLID": ["CELLNAME", "LOGICRNCID", "NODEBID", "NODEBNAME"]},
                                {"CELLID": ["CELLNAME", "LOGICRNCID", "NODEBID", "NODEBNAME"]},
                                {"ULOCELLID": ["CELLNAME", "LOGICRNCID", "NODEBID", "NODEBNAME"]},
                                {"LOCELL": ["CELLNAME", "LOGICRNCID", "NODEBID", "NODEBNAME"]},
                                {"LOCALCELLID": ["CELLNAME", "LOGICRNCID", "NODEBID", "NODEBNAME"]},
                                {"NODEBID": ["NODEBNAME"]}],
                      "CELL": [{"NRCELLID": ["CELLNAME"]}, {"CELLID": ["CELLNAME"]}, {"ULOCELLID": ["CELLNAME"]},
                               {"LOCELL": ["CELLNAME"]}, {"LOCALCELLID": ["CELLNAME"]}],
                      "ENODEBCELL": [{"NRCELLID": ["CELLNAME"]}, {"CELLID": ["CELLNAME"]}, {"ULOCELLID": ["CELLNAME"]},
                                     {"LOCELL": ["CELLNAME"]}, {"LOCALCELLID": ["CELLNAME"]}],
                      "NBIOTCELL": [{"NRCELLID": ["CELLNAME"]}, {"CELLID": ["CELLNAME"]},
                                    {"LOCALCELLID": ["CELLNAME"]}], "UTRANNCELL": [{"CELLID": ["LOCALCELLNAME"]}],
                      "NRCELL": [{"NRCELLID": ["CELLNAME"]}, {"CELLID": ["CELLNAME"]}, {"ULOCELLID": ["CELLNAME"]},
                                 {"LOCELL": ["CELLNAME"]}, {"LOCALCELLID": ["CELLNAME"]}],
                      "NRDUCELL": [{"NRDUCELLID": ["NRDUCELLNAME"]}, {"CELLID": ["NRDUCELLNAME"]},
                                   {"ULOCELLID": ["NRDUCELLNAME"]}, {"LOCELL": ["NRDUCELLNAME"]},
                                   {"LOCALCELLID": ["NRDUCELLNAME"]}],
                      "NODEBFUNCTION": [{"NODEBID": ["NODEBFUNCTIONNAME"]}],
                      "GBTSFUNCTION": [{"OBJID": ["GBTSFUNCTIONNAME"]}],
                      "ENODEBFUNCTION": [{"OBJID": ["ENODEBFUNCTIONNAME"]}],
                      "GNODEBFUNCTION": [{"OBJID": ["GNODEBFUNCTIONNAME"]}]}

        list_keys = ['NODEBFUNCTIONNAME', 'GBTSFUNCTIONNAME', 'ENODEBFUNCTIONNAME', 'GNODEBFUNCTIONNAME']

        try:
            for managedObject, namespace in self.getElements(filename, "MO"):
                document = dict()
                # Process all child nodes
                self.processMOAttr(managedObject, document)

                try:
                    for key in list_keys:
                        if key in document:
                            mappingKeys[key] = document[key]
                except KeyError as e:
                    logger.warning("Could not getNetworkMap from document due to {0}".format(e))
                    continue

                if prefixNe:
                    document["CLASSNAME"] = document["CLASSNAME"].upper().replace(prefixNe.upper(), "")

                if document["CLASSNAME"].upper() in unitsToGet.keys():
                    for corrDict in unitsToGet[document["CLASSNAME"].upper()]:
                        corrKey = corrDict.keys()[0]
                        if corrKey not in document.keys():
                            continue
                        if corrKey not in enrichmentData.keys():
                            enrichmentData[corrKey] = dict()

                        if document[corrKey] not in enrichmentData[corrKey].keys():
                            enrichmentData[corrKey][document[corrKey]] = dict()

                        for enrichKey in corrDict[corrKey]:
                            if enrichKey in document.keys():
                                enrichmentData[corrKey][document[corrKey]][enrichKey] = document[enrichKey]

            return enrichmentData, mappingKeys

        except etree.ParseError:
            logger.warning("Malformed HUAWEI Parameter GExport XML file '{0}'".format(filename))
            return enrichmentData

    def enrichField(self, sourceList, destField, newDocument, enrichDict):
        for key in sourceList:
            if key in enrichDict.keys() and key in newDocument.keys():
                if newDocument[key] in enrichDict[key].keys():
                    try:
                        if enrichDict[key][newDocument[key]][destField] not in ['', None]:
                            if destField not in newDocument.keys():
                                newDocument[destField] = enrichDict[key][newDocument[key]][destField]
                                return
                            newDocument[destField] = enrichDict[key][newDocument[key]][destField]
                            return
                    except:
                        pass

    def enrichDocument(self, newDocument, mongoDocument, enrichDict):
        # 2G
        if 'BTSNAME' in mongoDocument.keys() and 'BTSNAME' in newDocument.keys():
            newDocument['BTS_NAME'] = mongoDocument['BTSNAME']

        if 'BTSID' in newDocument.keys() and 'BTS_NAME' not in newDocument.keys():
            self.enrichField(['BTSID'], 'BTSNAME', newDocument, enrichDict)
            if 'BTSNAME' in newDocument.keys():
                newDocument['BTS_NAME'] = newDocument['BTSNAME']

        # 3G
        if 'RNCNAME' in mongoDocument.keys() and 'RNCNAME' in newDocument.keys():
            newDocument['RNC_NAME'] = mongoDocument['RNCNAME']
        elif 'CELLID' in enrichDict.keys() and 'CELLID' in newDocument.keys():
            if newDocument['CELLID'] in enrichDict['CELLID'].keys():
                if 'NODEBNAME' in enrichDict['CELLID'][newDocument['CELLID']]:
                    newDocument['NODEB_NAME'] = enrichDict['CELLID'][newDocument['CELLID']]['NODEBNAME']

        if 'NODEBNAME' in newDocument.keys() and 'NODEBID' in newDocument.keys() and 'NODEB_NAME' not in newDocument.keys():
            newDocument['NODEB_NAME'] = newDocument['NODEBNAME']
            try:
                mongoDocument["NODEB_NAME"] = newDocument["NODEBNAME"]
            except:
                pass

        elif 'NODEBID' in newDocument.keys() and 'NODEB_NAME' not in newDocument.keys():
            self.enrichField(['NODEBID'], 'NODEBFUNCTIONNAME', newDocument, enrichDict)
            if 'NODEBFUNCTIONNAME' in newDocument.keys():
                newDocument['NODEB_NAME'] = newDocument['NODEBFUNCTIONNAME']
                try:
                    mongoDocument["NODEB_NAME"] = newDocument["NODEBFUNCTIONNAME"]
                except:
                    pass
            else:
                self.enrichField(['NODEBID'], 'NODEBNAME', newDocument, enrichDict)
                if 'NODEBNAME' in newDocument.keys():
                    newDocument['NODEB_NAME'] = newDocument['NODEBNAME']
                    try:
                        mongoDocument["NODEB_NAME"] = newDocument["NODEBNAME"]
                    except:
                        pass

        # 4G
        if 'ENODEBFUNCTIONNAME' in mongoDocument.keys() and 'ENODEBFUNCTIONNAME' in newDocument.keys():
            newDocument['ENODEB_NAME'] = mongoDocument['ENODEBFUNCTIONNAME']

        if ('NRCELLID' in newDocument.keys() or 'CELLID' in newDocument.keys() or 'ULOCELLID' in newDocument.keys()
                or 'LOCELL' in newDocument.keys() or 'LOCALCELLID' in newDocument.keys()):
            self.enrichField(['NRCELLID', 'CELLID', 'ULOCELLID', 'LOCELL', 'LOCALCELLID'], 'CELLNAME',
                             newDocument, enrichDict)
            if 'CELLNAME' in newDocument.keys():
                newDocument['CELL_NAME'] = newDocument['CELLNAME']
            self.enrichField(['NRCELLID', 'CELLID', 'ULOCELLID', 'LOCELL', 'LOCALCELLID'], 'BTSID',
                             newDocument, enrichDict)
        # 5G
        if 'BTSNAME' in mongoDocument.keys() and 'GNODEBFUNCTIONNAME' in newDocument.keys():
            newDocument['GNODEB_NAME '] = mongoDocument['GNODEBFUNCTIONNAME']

        if 'NRDUCELLID' in newDocument.keys():
            self.enrichField(['NRDUCELLID'], 'NRDUCELLNAME', newDocument, enrichDict)
            if 'NRDUCELLNAME' in newDocument.keys():
                newDocument['CELL_NAME'] = newDocument['NRDUCELLNAME']
                newDocument['CELLNAME'] = newDocument['NRDUCELLNAME']
            self.enrichField(['NRDUCELLID'], 'BTSID', newDocument, enrichDict)

    def createMongoDocument(self, class_name, newDocument, mongoDocument, enrichDict):
        if class_name == 'ADJNODE':
            mongoDocument["ADJACENTNODEID"] = newDocument["ANI"]
            mongoDocument["ANI"] = newDocument["ANI"]

        if class_name in self._enrichMapping.keys():
            for key in self._enrichMapping[class_name]['fields']:
                if key not in enrichDict.keys() or key not in newDocument.keys():
                    # logger.warning('Item doesn't exist {0}'.format(key))
                    continue
                mongoDocument[key] = newDocument[key]

            for key in self._enrichMapping[class_name]['enrich'].keys():
                if key not in newDocument.keys():
                    continue
                for enrichKey in self._enrichMapping[class_name]['enrich'][key]:
                    if key not in enrichDict.keys():
                        # logger.warning('Failed to enrich {0}'.format(key))
                        continue
                    if newDocument[key] not in enrichDict[key].keys():
                        # logger.warning('Failed to enrich {0}'.format(key))
                        continue
                    if enrichKey not in enrichDict[key][newDocument[key]].keys():
                        # logger.warning('Failed to enrich {0}'.format(key))
                        continue

                    mongoDocument[enrichKey] = enrichDict[key][newDocument[key]][enrichKey]

            for copyDict in self._enrichMapping[class_name]['copy']:
                for key in copyDict.keys():
                    if key in newDocument.keys():
                        mongoDocument[copyDict[key]] = newDocument[key]
                        continue
                    elif key in mongoDocument.keys():
                        mongoDocument[copyDict[key]] = mongoDocument[key]
                        continue

                    # logger.warning('Faild to copy {0} - {1}'.format(key, class_name))
        if mongoDocument != dict():
            mongoDocument['CLASSNAME'] = class_name

    def cnoperatorParse(self, newDocument, mongoDocument):
        # 3G BSC6900UMTS files
        if "CNOPINDEX" in newDocument.keys() and "CNOPERATORNAME" in newDocument.keys():

            newDocument["CN_ID"] = newDocument["CNOPINDEX"]
            mongoDocument["CN_ID"] = newDocument["CN_ID"]
            try:
                newDocument["PLMN"] = self._MNC_directory[newDocument["MNC"]]
                mongoDocument["PLMN"] = newDocument["PLMN"]
            except KeyError:
                newDocument["PLMN"] = newDocument["CNOPERATORNAME"]
                mongoDocument["PLMN"] = newDocument["CNOPERATORNAME"]

        # Other files
        elif "CNOPERATORID" in newDocument.keys() and "CNOPERATORNAME" in newDocument.keys() and "ENODEBFUNCTIONNAME" in newDocument.keys():

            newDocument["CN_ID"] = newDocument["CNOPERATORID"]
            mongoDocument["CN_ID"] = newDocument["CNOPERATORID"]

            try:
                newDocument["PLMN"] = self._MNC_directory[newDocument["MNC"]]
                mongoDocument["PLMN"] = newDocument["PLMN"]
            except KeyError:
                newDocument["PLMN"] = newDocument["CNOPERATORNAME"]
                mongoDocument["PLMN"] = newDocument["CNOPERATORNAME"]

            newDocument["ENODEB_NAME"] = newDocument["ENODEBFUNCTIONNAME"]
            mongoDocument["ENODEB_NAME"] = newDocument["ENODEBFUNCTIONNAME"]

    def processFile(self, file_path_open, familyObj, baseObject, elementNameNe, prefixNe, typeNe, enrichDict,
                    mappingKeys, listMoDuplicated):

        dateTime, elementName, ip = self.getFilenameInfo(familyObj.fileName)
        listOfMerged = {}

        headerInfo = dict()
        headerInfo['DATETIME'] = dateTime
        headerInfo['ELEMENTNAME'] = elementName
        headerInfo['OBJECT'] = headerInfo['ELEMENTNAME']
        headerInfo['NE_NAME'] = headerInfo['ELEMENTNAME']
        headerInfo["BSC_NAME"] = headerInfo["ELEMENTNAME"]
        headerInfo["RNC_NAME"] = headerInfo["ELEMENTNAME"]

        try:
            timestamp = familyObj.parseEnvelopeDataTime(dateTime)
        except ValueError as e:
            logger.warning("Could not build mediationEnvelope due to {0}: ".format(e), __file__)

        if typeNe in ['BTS3900', 'BTS5900']:
            try:
                if 'NODEBFUNCTIONNAME' in mappingKeys:
                    tmp = self._mongoConnection.executeQuery(
                        {"FUNCTION": mappingKeys['NODEBFUNCTIONNAME'], "NODEBID": {'$exists': True}},
                        'find_one')
                    try:
                        if 'OBJECT' in tmp:
                            headerInfo['RNC_NAME'] = tmp['OBJECT']
                    except:
                        del headerInfo['RNC_NAME']
                else:
                    del headerInfo['RNC_NAME']
                if 'GBTSFUNCTIONNAME' in mappingKeys:
                    tmp = self._mongoConnection.executeQuery(
                        {"BTSNAME": mappingKeys['GBTSFUNCTIONNAME'], "BTSID": {'$exists': True}},
                        'find_one')
                    try:
                        if 'OBJECT' in tmp:
                            headerInfo['BSC_NAME'] = tmp['OBJECT']
                    except:
                        del headerInfo['BSC_NAME']
                else:
                    del headerInfo['BSC_NAME']

                if 'ENODEBFUNCTIONNAME' in mappingKeys:
                    headerInfo['ENODEB_NAME'] = mappingKeys['ENODEBFUNCTIONNAME']
                if 'GNODEBFUNCTIONNAME' in mappingKeys:
                    headerInfo['GNODEB_NAME'] = mappingKeys['GNODEBFUNCTIONNAME']

            except Exception as e:
                logger.warning('Error: {0}'.format(e))

        for managedObject, namespace in self.getElements(file_path_open, "MO"):
            # Initialize the object that represents what will be inserted in the BD
            mongoDocument = dict()
            createMongo = True
            familyObj.clearDocuments()
            isToMerge = False

            newDocument = copy.deepcopy(headerInfo)

            if typeNe in ['NodeB', 'LTE', 'BSC6900UMTS', 'BSC6910UMTS']:
                del newDocument["BSC_NAME"]
            if typeNe in ['NodeB', 'LTE', 'BSC6900GSM', 'BSC6910GSM', 'BSC6900GU']:
                del newDocument["RNC_NAME"]
            if typeNe in ['LTE']:
                newDocument["ENODEB_NAME"] = newDocument["ELEMENTNAME"]

            # Process all child nodes of MO
            self.processMOAttr(managedObject, newDocument)

            newDocument["CLASSNAME"] = managedObject.attrib["className"].upper().replace(prefixNe.upper(), "")
            newDocument["DATETIME"] = dateTime
            newDocument['GRANULARITY PERIOD'] = 1440
            # Insert the prefix
            newDocument["P"] = prefixNe.upper()
            newDocument["ELEMENTNAME"] = elementNameNe
            newDocument["NECLASSNAME"] = typeNe
            newDocument['FILTERPI'] = newDocument['NAME']

            # Validate is ClasseName need to be uniformization
            if typeNe in self._modelsMapping.keys() and newDocument["CLASSNAME"] in self._modelsMapping[typeNe].keys():
                newDocument["CLASSNAME"] = self._modelsMapping[typeNe][newDocument["CLASSNAME"]]

            # Create mongo document
            self.createMongoDocument(newDocument['CLASSNAME'], newDocument, mongoDocument, enrichDict)
            if mongoDocument == dict():
                createMongo = False

            # Enrichment of the document with MO hierarchy
            self.enrichDocument(newDocument, mongoDocument, enrichDict)

            try:
                if "," in managedObject.attrib["fdn"]:
                    parentFDN = managedObject.attrib["fdn"].rsplit(",", 1)[0]
                else:
                    parentFDN = ""
                newDocument["PARENTFDN"] = parentFDN

            except Exception, e:
                logger.warning("Missing attribute {0} in <MO> node in file \"{1}\"".format(e, familyObj.fileName))
                continue

            if newDocument["CLASSNAME"] == 'NE':
                newDocument["NENAME"] = newDocument["NAME"]
                document = newDocument.copy()
                document.update(headerInfo)
                document["CLASSNAME"] = "NEW_NE"
                document["NAME"] = newDocument["ELEMENTNAME"]
                document["NERMVERSION"] = newDocument["NEVERSION"]

                singlefamilyObj = FamilyObject()
                singlefamilyObj.fileName = familyObj.fileName
                singlefamilyObj.setUnitID("NEW_NE")
                singlefamilyObj.addDocument({"dataTime": timestamp, "granularitySec": 1440, "data": document})
                self.nextOp(familyObj=singlefamilyObj, baseObject=baseObject)

            if newDocument["CLASSNAME"] in ["CNOPERATOR", "UCNOPERATOR"]:
                self.cnoperatorParse(newDocument, mongoDocument)
                if 'ENODEBFUNCTIONNAME' not in newDocument.keys():
                    newDocument["ENODEBFUNCTIONNAME"] = newDocument["ELEMENTNAME"]

            # Ensure you put BTS_NAME and NODEB_NAME if they don't exist
            if typeNe in ['BTS3900', 'BTS5900']:
                if 'BTS_NAME' not in newDocument.keys() and 'GBTSFUNCTIONNAME' in mappingKeys:
                    newDocument['BTS_NAME'] = mappingKeys['GBTSFUNCTIONNAME']
                if 'NODEB_NAME' not in newDocument.keys() and 'NODEBFUNCTIONNAME' in mappingKeys:
                    newDocument['NODEB_NAME'] = mappingKeys['NODEBFUNCTIONNAME']

            if createMongo:
                newDocument.update(mongoDocument)
                self._mongoConnection.executeQuery(
                    {"query": {"CORRKEY": mongoDocument['CORRKEY']}, "set": mongoDocument}, 'upSert')

            # Send to kafka only if not to merged info
            moIdentifier = newDocument["CLASSNAME"] + '_' + managedObject.attrib["fdn"].upper()
            if moIdentifier in listMoDuplicated:
                isToMerge = True

            if not isToMerge:
                familyObj.setUnitID(newDocument["CLASSNAME"])
                familyObj.addDocument({"dataTime": timestamp, "granularitySec": 1440, "data": newDocument})
                self.nextOp(familyObj=familyObj, baseObject=baseObject)
            else:
                if moIdentifier not in listOfMerged:
                    listOfMerged[moIdentifier] = newDocument
                else:
                    listOfMerged[moIdentifier].update(newDocument)

        if listOfMerged:
            for doc in listOfMerged.values():
                familyObj.clearDocuments()
                familyObj.setUnitID(doc["CLASSNAME"])
                familyObj.addDocument({"dataTime": timestamp, "granularitySec": 1440, "data": doc})
                self.nextOp(familyObj=familyObj, baseObject=baseObject)