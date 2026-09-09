__doc__ = \
    '''
	Parser for HUAWEI Parameters GExport XML using sax
'''

__version__ = '0.1'

__authors__ = [
    "Version 1.0: Bruno Silva <bruno-e-silva@alticelabs.com>"
]

import io, re, os, json
import gzip
import copy
import HierarchyManager
from lxml import etree
import importlib
from datetime import datetime
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
            json.load(open('{0}/{1}/config.json'.format(config['location'], self.options['enrich'].replace('.', '/')))))
        self._mongoConnection = mongoCon(config)
        self._mongoConnection.getConnection()
        self._MNCdirectory = {'16': 'Oi', '24': 'Oi', '30': 'Oi', '31': 'Oi', '01': 'Vivo', '1': 'Vivo', '06': 'Vivo',
                              '6': 'Vivo', '10': 'Vivo', '11': 'Vivo', '23': 'Vivo', '02': 'TIM', '2': 'TIM',
                              '03': 'TIM', '3': 'TIM', '04': 'TIM', '4': 'TIM', '08': 'TIM', '8': 'TIM', '99': 'FAKE'}
        self._enrichMapping = json.load(open(
            '/opt/alticelabs/namf/src/shelf/collectorprocess/operators/Readers/HUAWEI/XML/GEXPORT/enrichMapping.json'),
                                        object_pairs_hook=OrderedDict)
        self._bitfieldParameters = json.load(open(
            '/opt/alticelabs/namf/src/shelf/collectorprocess/operators/Readers/HUAWEI/XML/GEXPORT/bitfieldParameters.json'))

    def process(self, familyObj=FamilyObject(), baseObject={}):
        logger.debug("[Reader] Reading HUAWEI Parameters GExport XML files' contents...")

        filePath = familyObj.getFiles()[0]
        familyObj.clearFiles()

        fileName = os.path.basename(filePath)
        familyObj.fileName = fileName

        try:
            # If file is compressed, replace the file path with a gzip buffered stream
            try:
                if filePath.endswith('.gz'):
                    enrichDict, mappingKeys = self.enrichData(gzip.open(filePath))
                    modelsMapping = json.load(open(
                        '/opt/alticelabs/namf/src/shelf/collectorprocess/operators/Readers/HUAWEI/XML/GEXPORT/modelsMapping.json'))
                    self.fast_iter(gzip.open(filePath), familyObj, baseObject, enrichDict, modelsMapping, mappingKeys)
                else:
                    enrichDict, mappingKeys = self.enrichData(filePath)
                    modelsMapping = json.load(open(
                        '/opt/alticelabs/namf/src/shelf/collectorprocess/operators/Readers/HUAWEI/XML/GEXPORT/modelsMapping.json'))
                    self.fast_iter(filePath, familyObj, baseObject, enrichDict, modelsMapping, mappingKeys)
            except etree.ParseError:
                logger.warning("EMPTY XML file '{0}'".format(filePath))
        except IOError:
            logger.warning("Could not open sample file \"{}\" in read mode: ".format(filePath), __file__)

    def fast_iter(self, f, familyObj, baseObject, enrichDict, modelsMapping, mappingKeys):
        context = iter(etree.iterparse(f, events=('start', 'end'), tag=('configData', 'class', 'object', 'parameter')))
        hm = HierarchyManager.HierarchyManager()

        headerInfo = dict()
        match = re.match('GExport_(?P<elementName>.+?)_(?P<ip>[^_]+)_(?P<dateTime>\d{10})\d{4}\.xml.*',
                         familyObj.fileName)

        headerInfo['DATETIME'] = (datetime.strptime(match.group('dateTime'), "%Y%m%d%H")).strftime('%Y-%m-%d %H:00:00')
        headerInfo['ELEMENTNAME'] = match.group('elementName')
        headerInfo['OBJECT'] = headerInfo['ELEMENTNAME']
        headerInfo['NE_NAME'] = headerInfo['ELEMENTNAME']
        headerInfo["BSC_NAME"] = headerInfo["ELEMENTNAME"]
        headerInfo["RNC_NAME"] = headerInfo["ELEMENTNAME"]
        headerInfo['GRANULARITY PERIOD'] = 1440
        try:
            timestamp = familyObj.parseEnvelopeDataTime(headerInfo['DATETIME'])
        except ValueError as e:
            logger.warning("Could not build mediationEnvelope due to {0}: ".format(e), __file__)

        first_object = True
        file_class_name = ''
        parse = True
        object_exists = False
        mongoDocument = dict()
        newDocument = dict()
        for event, elem in context:
            if event == 'start':
                if elem.tag == 'class':
                    name = elem.get('name').decode("latin-1")
                    if not file_class_name:
                        file_class_name = name.upper()
                        prefix_class_name = name.upper()
                        if name in ['BTS3900', 'BTS5900']:
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
                        continue
                    # ignorar primeiro class (nivel acima)

                    parse = True
                    if '_' in name:
                        class_name, prefix_class = self.processClass(name.upper())
                    else:
                        class_name = name.upper()
                        prefix_class = prefix_class_name.upper()

                    try:
                        class_name = modelsMapping[file_class_name][class_name]
                    except Exception as e:
                        # logger.warning("Could not map class_name \"{0}\": {1}".format(class_name, e))
                        pass
                    try:
                        if not hm.validateClass(class_name):
                            # logger.warning("Could not FDN map class_name \"{0}\": {1}".format(class_name, e))
                            parse = False
                    except Exception as e:
                        # logger.warning("Something went wrong with class_name \"{0}\": {1}".format(class_name, e))
                        parse = False

                elif elem.tag == 'object' and parse:
                    if first_object:
                        familyObj.clearDocuments()
                        familyObj.setUnitID("NEW_NE")
                        newDocument = copy.deepcopy(headerInfo)
                        newDocument["NECLASSNAME"] = file_class_name
                        newDocument["CLASSNAME"] = "NEW_NE"
                        newDocument["P"] = file_class_name
                        newDocument["NAME"] = newDocument["ELEMENTNAME"]
                        newDocument["NERMVERSION"] = elem.attrib["version"]

                        hm.buildFDN(newDocument)
                        mongoDocument = dict()
                        self.enrichDocument(newDocument["CLASSNAME"], newDocument, mongoDocument, enrichDict)
                        if mongoDocument != dict():
                            self._mongoConnection.executeQuery(
                                {"query": {"CORRKEY": mongoDocument['CORRKEY']}, "set": mongoDocument}, 'upSert')
                        familyObj.addDocument({"dataTime": timestamp, "granularitySec": 1440, "data": newDocument})
                        self.nextOp(familyObj=familyObj, baseObject=baseObject)
                        first_object = False
                        continue

                    object_exists = True
                    newDocument = copy.deepcopy(headerInfo)
                    newDocument["NECLASSNAME"] = file_class_name
                    newDocument["CLASSNAME"] = class_name
                    newDocument["P"] = prefix_class
                    if newDocument["NECLASSNAME"] in ['NodeB', 'LTE', 'BSC6900UMTS', 'BSC6910UMTS']:
                        del newDocument["BSC_NAME"]
                    if newDocument["NECLASSNAME"] in ['NodeB', 'LTE', 'BSC6900GSM', 'BSC6910GSM', 'BSC6900GU']:
                        del newDocument["RNC_NAME"]
                    if newDocument["NECLASSNAME"] in ['LTE']:
                        # print newDocument["NECLASSNAME"]
                        newDocument["ENODEB_NAME"] = newDocument["ELEMENTNAME"]
                    elem.clear()

                elif elem.tag == 'parameter' and parse:
                    try:
                        param_name = elem.get('name').decode("latin-1").upper()
                        param_value = elem.get('value').decode("latin-1")
                        if newDocument.has_key(param_name):
                            logger.warning("Duplicated parameter name '{0}'".format(param_name))
                            continue
                        # Bitfield parameters
                        elif param_name.upper() in self._bitfieldParameters[class_name].keys():
                            newDocument[param_name] = param_value
                            values = param_value.split("&")
                            for value in values:
                                bfieldRegex = re.match('(?P<FIELD>[^&;]+)-(?P<VALUE>\d)', value)
                                # newDocument[bfieldRegex.group('FIELD').upper()] = bfieldRegex.group('VALUE')
                                # fix duplicate columns for two different params, so they're correctly associated with the param if the mapping exists. if not, follows old behavior
                                field = bfieldRegex.group('FIELD').upper()
                                if param_name.upper() + '_' + field in self._bitfieldParameters[class_name][
                                    param_name.upper()]:
                                    newDocument[param_name.upper() + '_' + field] = bfieldRegex.group('VALUE')
                                else:
                                    newDocument[field] = bfieldRegex.group('VALUE')
                        else:
                            newDocument[param_name] = param_value
                    except Exception as e:
                        try:
                            param_name = elem.get('name').decode("latin-1").upper()
                            param_value = elem.get('value').encode('utf-8', 'ignore').decode('utf-8')
                            newDocument[param_name] = param_value
                            # Bitfield parameters
                            if param_name.upper() in self._bitfieldParameters[class_name].keys():
                                values = param_value.split("&")
                                for value in values:
                                    bfieldRegex = re.match('(?P<FIELD>[^&;]+)-(?P<VALUE>\d)', value)
                                    # newDocument[bfieldRegex.group('FIELD').upper()] = bfieldRegex.group('VALUE')
                                    # fix duplicate columns for two different params, so they're correctly associated with the param if the mapping exists. if not, follows old behavior
                                    field = bfieldRegex.group('FIELD').upper()
                                    if param_name.upper() + '_' + field in self._bitfieldParameters[class_name][
                                        param_name.upper()]:
                                        newDocument[param_name.upper() + '_' + field] = bfieldRegex.group('VALUE')
                                    else:
                                        newDocument[field] = bfieldRegex.group('VALUE')
                        except:
                            pass  # logger.warning('Value not accepted: {0}'.format(e))

            elif event == 'end':
                if elem.tag == 'object' and object_exists and parse:
                    newDocument = hm.buildFDN(newDocument)

                    mongoDocument = dict()
                    self.enrichDocument(newDocument["CLASSNAME"], newDocument, mongoDocument, enrichDict)
                    createMongo = True
                    if mongoDocument == dict():
                        createMongo = False

                    if newDocument["CLASSNAME"] in ["CNOPERATOR", "UCNOPERATOR"]:
                        self.cnoperatorParse(newDocument, mongoDocument)
                        if 'ENODEBFUNCTIONNAME' not in newDocument.keys():
                            newDocument["ENODEBFUNCTIONNAME"] = newDocument["ELEMENTNAME"]

                        # print newDocument.keys()
                    # if 'NODEBNAME' in newDocument.keys():
                    # mongoDocument["NODEB_NAME"] = newDocument["NODEBNAME"]

                    # 2G
                    if 'BTSNAME' in mongoDocument.keys() and 'BTSNAME' in newDocument.keys():
                        newDocument['BTS_NAME'] = mongoDocument['BTSNAME']
                    # 3G
                    if 'RNCNAME' in mongoDocument.keys() and 'RNCNAME' in newDocument.keys():
                        newDocument['RNC_NAME'] = mongoDocument['RNCNAME']
                    elif 'CELLID' in enrichDict.keys() and 'CELLID' in newDocument.keys():
                        if newDocument['CELLID'] in enrichDict['CELLID'].keys():
                            if 'NODEBNAME' in enrichDict['CELLID'][newDocument['CELLID']]:
                                newDocument['NODEB_NAME'] = enrichDict['CELLID'][newDocument['CELLID']]['NODEBNAME']

                    # 4G
                    if 'ENODEBFUNCTIONNAME' in mongoDocument.keys() and 'ENODEBFUNCTIONNAME' in newDocument.keys():
                        newDocument['ENODEB_NAME'] = mongoDocument['ENODEBFUNCTIONNAME']
                    # 5G
                    if 'BTSNAME' in mongoDocument.keys() and 'GNODEBFUNCTIONNAME' in newDocument.keys():
                        newDocument['GNODEB_NAME '] = mongoDocument['GNODEBFUNCTIONNAME']

                    if (
                            'NRCELLID' in newDocument.keys() or 'CELLID' in newDocument.keys() or 'ULOCELLID' in newDocument.keys() or 'LOCELL' in newDocument.keys() or 'LOCALCELLID' in newDocument.keys()):
                        self.enrichField(['NRCELLID', 'CELLID', 'ULOCELLID', 'LOCELL', 'LOCALCELLID'], 'CELLNAME',
                                         newDocument, enrichDict)
                        if 'CELLNAME' in newDocument.keys():
                            newDocument['CELL_NAME'] = newDocument['CELLNAME']
                        self.enrichField(['NRCELLID', 'CELLID', 'ULOCELLID', 'LOCELL', 'LOCALCELLID'], 'BTSID',
                                         newDocument, enrichDict)

                    if ('NRDUCELLID' in newDocument.keys()):
                        self.enrichField(['NRDUCELLID'], 'NRDUCELLNAME', newDocument, enrichDict)
                        if 'NRDUCELLNAME' in newDocument.keys():
                            newDocument['CELL_NAME'] = newDocument['NRDUCELLNAME']
                            newDocument['CELLNAME'] = newDocument['NRDUCELLNAME']
                        self.enrichField(['NRDUCELLID'], 'BTSID', newDocument, enrichDict)

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

                    if 'BTSID' in newDocument.keys() and 'BTS_NAME' not in newDocument.keys():
                        self.enrichField(['BTSID'], 'BTSNAME', newDocument, enrichDict)
                        if 'BTSNAME' in newDocument.keys():
                            newDocument['BTS_NAME'] = newDocument['BTSNAME']

                    # additional db info for BTS_NAME and NODEB_NAME if not yet existent:
                    if file_class_name in ['BTS3900', 'BTS5900']:
                        if 'BTS_NAME' not in newDocument.keys() and 'GBTSFUNCTIONNAME' in mappingKeys:
                            newDocument['BTS_NAME'] = mappingKeys['GBTSFUNCTIONNAME']
                        if 'NODEB_NAME' not in newDocument.keys() and 'NODEBFUNCTIONNAME' in mappingKeys:
                            newDocument['NODEB_NAME'] = mappingKeys['NODEBFUNCTIONNAME']

                    if createMongo:
                        newDocument.update(mongoDocument)
                        self._mongoConnection.executeQuery(
                            {"query": {"CORRKEY": mongoDocument['CORRKEY']}, "set": mongoDocument}, 'upSert')

                    familyObj.clearDocuments()
                    familyObj.setUnitID(newDocument["CLASSNAME"])
                    familyObj.addDocument({"dataTime": timestamp, "granularitySec": 1440, "data": newDocument})
                    self.nextOp(familyObj=familyObj, baseObject=baseObject)

                    elem.clear()
                elif elem.tag == 'class':
                    parse = True
                if elem.tag == 'object':
                    object_exists = False
            else:
                elem.clear()
        del context

    def enrichData(self, filePath):
        enrichmentData = dict()
        mappingKeys = dict()
        try:
            context = iter(etree.iterparse(filePath, events=('start', 'end'), tag=('class', 'object', 'parameter')))
        except etree.ParseError:
            logger.warning("Malformed HUAWEI Parameter GExport XML file '{0}'".format(filePath))
            return enrichmentData

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

        parametersData = dict()
        file_class_name = ''
        toProcess = False
        for event, elem in context:
            if event == 'start':
                if elem.tag == 'class':
                    name = elem.get('name').decode("latin-1")
                    if not file_class_name:
                        file_class_name = name.upper()
                        continue

                    if '_' in name:
                        class_name, prefix_class = self.processClass(name.upper())
                    else:
                        class_name = name.upper()
                        prefix_class = file_class_name.upper()

                    if class_name in unitsToGet.keys():
                        toProcess = True

                if elem.tag == 'parameter' and toProcess:
                    try:
                        parametersData[elem.get('name').decode("latin-1").upper()] = elem.get('value').decode("latin-1")
                        if elem.get('name').decode("latin-1").upper() in ['NODEBFUNCTIONNAME', 'GBTSFUNCTIONNAME',
                                                                          'ENODEBFUNCTIONNAME', 'GNODEBFUNCTIONNAME']:
                            mappingKeys[elem.get('name')] = elem.get('value').decode("latin-1")
                    except UnicodeError:
                        try:
                            # encoding before decoding is able to bypass the ascii error but keeps weird characters
                            # both decoding methods work
                            # ele_val = elem.get('value').encode('iso-8859-1').decode('latin-1')
                            # ele_val = elem.get('value').encode('utf-8', 'ignore').decode('utf-8')
                            ele_val = "Discarded content"
                            parametersData[elem.get('name').decode("latin-1").upper()] = ele_val
                            if elem.get('name').decode("latin-1").upper() in ['NODEBFUNCTIONNAME', 'GBTSFUNCTIONNAME',
                                                                              'ENODEBFUNCTIONNAME',
                                                                              'GNODEBFUNCTIONNAME']:
                                mappingKeys[elem.get('name')] = ele_val
                        except UnicodeError:
                            pass  # discarded value

            elif event == 'end':
                if elem.tag == 'class':
                    toProcess = False
                    class_name = ''
                    parametersData = dict()

                if elem.tag == 'object' and toProcess:
                    for corrDict in unitsToGet[class_name]:
                        corrKey = corrDict.keys()[0]
                        if corrKey not in parametersData.keys():
                            continue
                        if corrKey not in enrichmentData.keys():
                            enrichmentData[corrKey] = dict()

                        if parametersData[corrKey] not in enrichmentData[corrKey].keys():
                            enrichmentData[corrKey][parametersData[corrKey]] = dict()

                        for enrichKey in corrDict[corrKey]:
                            if enrichKey in parametersData.keys():
                                enrichmentData[corrKey][parametersData[corrKey]][enrichKey] = parametersData[enrichKey]
                elem.clear()
        del context
        return enrichmentData, mappingKeys

    def processClass(self, name):
        name = name.rsplit("_", 1)
        class_name = name[0]
        prefix_class = name[1]
        return class_name, prefix_class

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

    def enrichDocument(self, class_name, newDocument, mongoDocument, enrichDict):

        if class_name == 'ADJNODE':
            mongoDocument["ADJACENTNODEID"] = newDocument["ANI"]
            mongoDocument["ANI"] = newDocument["ANI"]

        if class_name in self._enrichMapping.keys():
            for key in self._enrichMapping[class_name]['fields']:
                if key not in enrichDict.keys() or key not in newDocument.keys():
                    # logger.warning('Item doesnt exist {0}'.format(key))
                    continue
                mongoDocument[key] = newDocument[key]

            for key in self._enrichMapping[class_name]['enrich'].keys():
                if key not in newDocument.keys():
                    continue
                for enrichKey in self._enrichMapping[class_name]['enrich'][key]:
                    if key not in enrichDict.keys():
                        # logger.warning('Faild to enrich {0}'.format(key))
                        continue
                    if newDocument[key] not in enrichDict[key].keys():
                        # logger.warning('Faild to enrich {0}'.format(key))
                        continue
                    if enrichKey not in enrichDict[key][newDocument[key]].keys():
                        # logger.warning('Faild to enrich {0}'.format(key))
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
                newDocument["PLMN"] = self._MNCdirectory[newDocument["MNC"]]
                mongoDocument["PLMN"] = newDocument["PLMN"]
            except KeyError:
                newDocument["PLMN"] = newDocument["CNOPERATORNAME"]
                mongoDocument["PLMN"] = newDocument["CNOPERATORNAME"]

        # Other files
        elif "CNOPERATORID" in newDocument.keys() and "CNOPERATORNAME" in newDocument.keys() and "ENODEBFUNCTIONNAME" in newDocument.keys():

            newDocument["CN_ID"] = newDocument["CNOPERATORID"]
            mongoDocument["CN_ID"] = newDocument["CNOPERATORID"]

            try:
                newDocument["PLMN"] = self._MNCdirectory[newDocument["MNC"]]
                mongoDocument["PLMN"] = newDocument["PLMN"]
            except KeyError:
                newDocument["PLMN"] = newDocument["CNOPERATORNAME"]
                mongoDocument["PLMN"] = newDocument["CNOPERATORNAME"]

            newDocument["ENODEB_NAME"] = newDocument["ENODEBFUNCTIONNAME"]
            mongoDocument["ENODEB_NAME"] = newDocument["ENODEBFUNCTIONNAME"]
