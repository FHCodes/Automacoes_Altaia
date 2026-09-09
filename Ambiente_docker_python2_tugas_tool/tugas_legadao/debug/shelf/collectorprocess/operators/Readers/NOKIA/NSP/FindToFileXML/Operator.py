#!/usr/bin/env python

__doc__ = \
    '''
    logToFileResponse Reader.
    Spec file syntax:
    <operation type="Readers" name="NOKIA.NSP.FindToFileXML" />
    '''

__version__ = '0.1'

__authors__ = [
    "Version 0.1: Francisco Santiago <francisco-j-santiago@telecom.pt>"
    "Version 1.0: Joao Pio <joao-t-pio@alticelabs.com>"
]

# Native libraries
import xml.etree.cElementTree as ET
import re
import os
import time
import datetime
import importlib

# Local libraries
BaseOperator = importlib.import_module("shelf.collectorprocess.operators.BaseOperator").BaseOperator
FamilyObject = importlib.import_module("shelf.collectorprocess.operators.FamilyObject").FamilyObject
logger = importlib.import_module("shelf.collectorprocess.logger").logger


class Operator(BaseOperator):

    # Class Constructor
    def __init__(self, operationParams, baseObject={}):
        BaseOperator.__init__(self, operationParams, baseObject=baseObject)

        self.node_tag_regex = re.compile("^\{.*?\}(.*?)LogRecord")

    @staticmethod
    def convert(info, baseObject={}):
        applied = False

        try:
            itemID = info["itemID"]
        except KeyError, e:
            logger.warning("KeyError: {0} is not a key".format(e))
            return applied
        except TypeError, e:
            logger.warning(e)
            return applied

        try:
            value = info["document"][info["itemID"]]

            if len(value) > 10:
                newValue = int(value[:10])
            else:
                newValue = int(value)

            newValue = datetime.datetime.fromtimestamp(newValue)
            newValue = newValue.strftime('%Y-%m-%d %H:%M:%S')
            info["document"].update({itemID: newValue})

            applied = True
        except TypeError, e:
            logger.warning(e)
            return applied
        except ValueError, e:
            logger.warning(e)
            return applied

        return applied

    @staticmethod
    def get_elements(filename_or_file, tag):

        context = iter(ET.iterparse(filename_or_file, events=('start', 'end', 'start-ns', 'end-ns')))
        namespace = tuple()

        for event, elem in context:
            # Start of a namespace
            if event == 'start-ns':
                namespace = (elem[0], elem[1])

            # End of a namespace
            elif event == 'end-ns':
                namespace = tuple()

            # Start of a XML node
            elif event == 'start':
                pass

            # End of a XML node
            elif event == 'end' and len(namespace) != 0:
                if elem.tag == "{{{0}}}{1}".format(namespace[1], tag):
                    yield elem, namespace
                    # preserve memory
                    elem.clear()

        # Rewind in case it is a file type
        if isinstance(filename_or_file, file):
            filename_or_file.rewind()

    def process(self, familyObj=FamilyObject(), baseObject={}):

        files_to_process = familyObj.getFiles()
        familyObj.clearDocuments()

        logger.debug("Reading NOKIA NSP XML files' contents...", __file__)

        for file_path in files_to_process:

            logger.debug("Processing '{0}'".format(file_path), __file__)

            # get_elements returns a generator, so must be invoked directly in a for loop
            for lognode, namespace in self.get_elements(file_path, "logToFileResponse"):

                fobs_dict = {}

                text_namespace = '{' + namespace[1] + '}'

                # Get all nodes of all families
                nodes = lognode.findall("*")
                for node in nodes:

                    # Identify the family from the node tag
                    try:
                        unit_id = self.node_tag_regex.match(node.tag).group(1)
                    except AttributeError:
                        logger.error("File {0} contains unrecognizable family {1} in its contents. Skipping to next node."
                                         .format(familyObj.fileName, node.tag), __file__)
                        continue

                    # Get file's name
                    familyObj.fileName = os.path.basename(file_path)
                    # Set the unit ID from the node tag
                    familyObj.setUnitID(unit_id)

                    document = dict()

                    # Get each counter of this family
                    for item in node.findall("*"):

                        if item.text:
                            document[item.tag.replace(text_namespace, "").upper()] = item.text.strip()

                        else:
                            document[item.tag.replace(text_namespace, "").upper()] = ""

                        for subItem in item.findall("*"):
                            if subItem.text:
                                document[item.tag.upper()] += ";{0}".format(subItem.text.strip())

                    try:
                        mode = self.options["mode"]

                        if mode.upper() == "POLICER":
                            if 'POLICERID' in document.keys():
                                familyObj.setUnitID('{0}.{1}'.format(familyObj.unitID, 'POLICER'))
                            elif 'QUEUEID' in document.keys():
                                familyObj.setUnitID('{0}.{1}'.format(familyObj.unitID, 'QUEUE'))
                    except KeyError:
                        pass

                    # Prepare the document for NAMF consumption
                    try:
                        # UM READER NAO DEVE MANIPULAR O CONTEUDO DOS CAMPOS, ESTA OPERACAO FAZIA SE FACILMENTE NO CATALOGO.
                        # FICOU ASSIM PORQUE FOI PRODUTIZADO NA OI E SO FOI DETETADO O PROBLEMA NA MEO
                        # Check if date is available
                        time_captured = int(document["TIMECAPTURED"]) / 1000

                        # Salvaguardar valor original de TIMECAPTURED para a MEO. NA Oi este campo e Timestamp e na MEO NUMBER
                        document["ORIGINAL_TIMECAPTURED"] = document["TIMECAPTURED"]

                        # Campo necessario para a MEO. Tem de se validar se o ficheiro tem timerecorded
                        if "TIMERECORDED" in document and "TIMECAPTURED" in document:
                            document["MEO_GRANULARITYPRD"] = int(document["TIMECAPTURED"]) - int(
                                document["TIMERECORDED"])
                        else:
                            document["MEO_GRANULARITYPRD"] = ""

                        # Convert to a timestamp Aqui esta-se a converter isto para GMT. Deveria ser feito em catalogo.
                        document["TIMECAPTURED"] = time.strftime('%Y-%m-%d %H:%M:%S',
                                                                 time.gmtime(time_captured))

                        ####################################FIM DE MANIPULACAO###########################################

                        # Parse the date
                        data_time = familyObj.parseEnvelopeDataTime(document["TIMECAPTURED"])
                        # no granularity period available, just create one
                        granularity_sec = "60"
                    except ValueError as e:
                        logger.error(
                            "Could not build mediationEnvelope due to {0}: ".format(e), __file__)
                        continue
                    except KeyError as e:
                        logger.error(
                            "Could not build mediationEnvelope due to {0}: ".format(e), __file__)

                    familyObj.addDocument(
                        {"dataTime": data_time, "granularitySec": granularity_sec, "data": document})

                    self.nextOp(familyObj=familyObj, baseObject=baseObject)
                    familyObj.clearDocuments()
