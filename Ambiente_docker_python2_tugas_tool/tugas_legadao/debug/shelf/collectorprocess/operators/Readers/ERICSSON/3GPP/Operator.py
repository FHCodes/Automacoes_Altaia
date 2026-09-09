#!/usr/bin/env python

__doc__ = \
    '''
    ERICSSON 3GPP 32.XXX Performance XML reader

    Spec file syntax:
    <operation type="Readers" name="ERICSSON.3GPP" consolidation="True" />
'''

__version__ = '1.0'

__authors__ = [
    "Version 1.0: Joao Pio <joao-t-pio@alticelabs.com>"
]

# Native libraries
import xml.etree.cElementTree as ET
import os
import gzip
import collections
from datetime import timedelta, datetime
import io
import cStringIO
import re
import importlib

# Local libraries
BaseOperator = importlib.import_module("shelf.collectorprocess.operators.BaseOperator").BaseOperator
FamilyObject = importlib.import_module("shelf.collectorprocess.operators.FamilyObject").FamilyObject
logger = importlib.import_module("shelf.collectorprocess.logger").logger


class Operator(BaseOperator):

    # Class Constructor
    def __init__(self, operationParams, baseObject={}):
        BaseOperator.__init__(self, operationParams, baseObject=baseObject)

        self._incubation_queue_401 = collections.OrderedDict()
        self._incubation_queue_432 = collections.OrderedDict()
        self._mature_queue_401 = dict()
        self._mature_queue_432 = dict()
        self._max_docs_in_incubation_cache = 100000
        self._max_docs_in_mature_cache = 1000

        self.datetime_regex = re.compile(r'^(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}).*$')
        self.parse_432_date_regex = re.compile(r'^(\d{4})-(\d{2})-(\d{2})[T ](\d{2}):(\d{2}):(\d{2}).*$')
        self.parse_401_date_regex = re.compile(r'^(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})[Z]*$')

        self.moid_401_regex = re.compile(r'^.*,([^=]+)=.*$')
        self.moid_432_regex = re.compile(r'^(.*,([^\.]*?)(=|\.).*?$)|((.*?)\..*?$)')

        self.fformat_regex = re.compile(r'^(32\.\d+) (V\d+\.\d+)$')

        self.namespace_regex = re.compile(r'^({.*}).*$')
        self.nedn_regex = re.compile(r'^.*MeContext=([^,]+).*$')
        self.unitid_regex = re.compile(r'(.*,(?P<unitid1>[^\.]*?)(=|\.).*?$)|((?P<unitid2>.*?)\..*?$)')
        self.measobjtype_regex = re.compile(r'([^=*]*,)|([^=]*)$')
        self.sectorcarrier_regex1 = re.compile("(.*?)([1-6])$")
        self.sectorcarrier_regex2 = re.compile(r'^.*SectorCarrier=([^,]+)$')
        self.pmflex_regex = re.compile(r'PMFLEX.*')
        self.pmflex_prefix_regex = re.compile(r'^(PMFLEX.*_PLMN)(.*?)(QCI\d)*$')
        self.mecontext_regex = re.compile(r'^T.*')
        self.wrongmecontext_regex = re.compile(r'^M(.*)$')

        self.sc_nen_dict = {"TIM_A": "A", "TIM_B": "B", "TIM_C": "C", "OI_A": "1", "OI_B": "2", "OI_C": "3"}
        self.sc_nen_dict2 = {"1": "1", "2": "2", "3": "3", "4": "A", "5": "B", "6": "C"}
        self.sc_nen_dict3 = {"1": "1", "2": "2", "3": "3", "4": "4", "5": "5", "6": "6"}

        # Initialize end time and gp cache
        self.time_cache = dict()

        # Initialize unit_id source flag according to spec file
        # This only applies to 32.435
        self._unit_source = "moid"
        if "unit_source" in self.options:
            if self.options["unit_source"].upper() == "FILENAME":
                self.use_end_time = "filename"

        # Initialize consolidation flag according to spec file
        self.consolidation = True
        if "consolidation" in self.options:
            if self.options["consolidation"].upper() == "TRUE":
                self.consolidation = True

        self._n_docs_in_cache = 0
        self.repeated_keys = 0

        # Create the specification of the 3GPP format
        self.format = {"standard": None, "v": None, "dtd": None}
        self.format_parser = None

    # Rewinds a buffered reader, does nothing if not a buffered reader
    @staticmethod
    def rewindFile(buffered_reader):
        if isinstance(buffered_reader, (io.BufferedReader, cStringIO.InputType)):
            try:
                buffered_reader.seek(0)
            except AttributeError as e:
                logger.error("Could not rewind the unzipped stream of due to {0}".format(e.message))

    @property
    def unit_source(self):
        return self._unit_source

    @unit_source.setter
    def unit_source(self, value):
        self._unit_source = value

    @property
    def max_docs_in_mature_cache(self):
        return self._max_docs_in_mature_cache

    @max_docs_in_mature_cache.setter
    def max_docs_in_mature_cache(self, value):
        self._max_docs_in_mature_cache = value

    @property
    def mature_queue_401(self):
        return self._mature_queue_401

    @mature_queue_401.setter
    def mature_queue_401(self, value):
        self._mature_queue_401 = value

    @property
    def mature_queue_432(self):
        return self._mature_queue_432

    @mature_queue_432.setter
    def mature_queue_432(self, value):
        self._mature_queue_432 = value

    @property
    def n_docs_in_cache(self):
        return self._n_docs_in_cache

    @n_docs_in_cache.setter
    def n_docs_in_cache(self, value):
        self._n_docs_in_cache = value

    @property
    def incubation_queue_401(self):
        return self._incubation_queue_401

    @incubation_queue_401.setter
    def incubation_queue_401(self, value):
        self._incubation_queue_401 = value

    @property
    def incubation_queue_432(self):
        return self._incubation_queue_432

    @incubation_queue_432.setter
    def incubation_queue_432(self, value):
        self._incubation_queue_432 = value

    @property
    def max_docs_in_incubation_cache(self):
        return self._max_docs_in_incubation_cache

    @max_docs_in_incubation_cache.setter
    def max_docs_in_incubation_cache(self, value):
        self._max_docs_in_incubation_cache = value

    @staticmethod
    def get_elements(filename_or_file, tag):

        if isinstance(filename_or_file, (io.BufferedReader, cStringIO.InputType)):
            try:
                filename_or_file.seek(0)
            except AttributeError as e:
                logger.error("Could not rewind the unzipped stream of due to {0}".format(e.message))

        context = iter(ET.iterparse(filename_or_file, events=('start', 'end')))
        _, root = next(context)  # get root element
        for event, elem in context:
            if '}' in elem.tag:
                targettag = elem.tag.rsplit("}", 1)[-1]
            else:
                targettag = elem.tag

            if event == 'end' and targettag == tag:
                yield elem
                root.clear()  # preserve memory

    @staticmethod
    def format_interval(value, base_format, unit_format):

        matrix_data = {
            'S':
                {
                    'S':
                        {
                            'value': 1,
                            'operation': ''
                        },
                    'M':
                        {
                            'value': 60,
                            'operation': '/'
                        },
                    'H':
                        {
                            'value': 3600,
                            'operation': '/'
                        }
                },
            'M':
                {
                    'S':
                        {
                            'value': 60,
                            'operation': '*'
                        },
                    'M':
                        {
                            'value': 1,
                            'operation': ''
                        },
                    'H':
                        {
                            'value': 60,
                            'operation': '/'
                        }
                },
            'H':
                {
                    'S':
                        {
                            'value': 3600,
                            'operation': '*'
                        },
                    'M':
                        {
                            'value': 60,
                            'operation': '*'
                        },
                    'H':
                        {
                            'value': 1,
                            'operation': ''
                        }
                }
        }

        if matrix_data[base_format][unit_format]['operation'] == '*':
            return value * matrix_data[base_format][unit_format]['value']
        elif matrix_data[base_format][unit_format]['operation'] == '/':
            return value / matrix_data[base_format][unit_format]['value']
        return value

    @staticmethod
    def parse_timezone(file_name):

        # fileName Ex: A20131014.0000-0300-0015-0300_SubNetwork=ONRM_ROOT_MO,SubNetwork=RNCCTA1,MeContext=RNCCTA1_statsfile.xml
        if "_" in file_name:
            temp_tz = file_name.split("_")[0]

            # tmpTZ Ex: A20131014.0000-0300-0015-0300
            if "." in temp_tz:
                temp_tz = temp_tz.split(".")[-1]

                # tmpTZ Ex: 0015-0300-0030-0300
                if "-" in temp_tz:
                    temp_tz = temp_tz.split("-")

                    # tmpTZ Ex: ["0015", "0300", "0030", "0300"]
                    if len(temp_tz) == 4:
                        time_zone = temp_tz[-1]

        # Converts timeZone from string to integer
        try:
            time_zone = time_zone.rstrip("0")
            time_zone = int(time_zone)
        except:
            time_zone = 0

        return time_zone

    def get_node_namespace(self, node):

        namespace = ""

        try:
            match = self.namespace_regex.match(node.tag)
            if match is not None:
                namespace = match.group(1)
        except Exception:
            return namespace

        return namespace

    @staticmethod
    def get_node_text(node):
        if not node.text:
            node.text = ""
        else:
            node.text = node.text.strip()

        return node.text

    @staticmethod
    def get_tz(file_name):
        # fileName Ex: A20131014.0000-0300-0015-0300_SubNetwork=ONRM_ROOT_MO,SubNetwork=RNCCTA1,MeContext=RNCCTA1_statsfile.xml
        #              M_A20211025.1100-0300-1115-0300_SubNetwork_ONRM_ROOT_MO_SubNetwork_MGLUE-GPRHUA-SGS02_MeContext_TVLT1_MG_statsfile.xml

        # Search the timeZone and converts timeZone from string to integer
        try:
            return int((re.match('^.*A\d+.\d{4}-(?P<tz>\d{2})00-.*$', file_name)).group('tz'))
        except Exception as e:
            return 0

    @staticmethod
    def get_date_401(date_str, time_zone):

        tmp_date_time = date_str.replace("Z", "")
        ts_list = re.findall(r"(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})", tmp_date_time)

        # If the date wasn't correctly parsed, raise an error.
        if ts_list and len(ts_list[0]) >= 6:
            # Create date string with TIMESTAMP format
            tmp_date_time = "{0}-{1}-{2} {3}:{4}:{5}".format(ts_list[0][0], ts_list[0][1], ts_list[0][2], ts_list[0][3],
                                                             ts_list[0][4], ts_list[0][5])
            date_time = tmp_date_time

        # Generate date from YYYY, MM, DD, HH, mm, ss
        d = datetime(int(ts_list[0][0]), int(ts_list[0][1]), int(ts_list[0][2]), int(ts_list[0][3]), int(ts_list[0][4]),
                     int(ts_list[0][5]))
        # Subtract a number of hours equal to the time
        date_time = d - timedelta(hours=time_zone)
        date_time = str(date_time)

        return date_time

    def generate_measobjtype(self, measured_object_id):

        try:
            tmp = self.measobjtype_regex.sub('', measured_object_id)
            measured_object_type = (tmp.replace('=', '-'))[:len(tmp) - 1]
        except Exception:
            measured_object_type = ""

        return measured_object_type

    def treatment_sectorcarrier(self, document):

        try:
            # Extract sectorcarrier from measuredobjectid
            sc_match = self.sectorcarrier_regex2.match(document["MEASUREDOBJECTID"])

            if sc_match is not None:
                sector_carrier = sc_match.group(1)
            else:
                logger.debug("Regex couldn't extract SECTORCARRIER from MEASUREDOBJECTID", __file__)
                return

            # Extract MeContext from NEDISTINGUISHEDNAME
            mecontext_match = self.nedn_regex.match(document["NEDISTINGUISHEDNAME"])

            if mecontext_match is not None:
                mecontext = mecontext_match.group(1)
            else:
                logger.debug("Regex couldn't extract MECONTEXT from NEDISTINGUISHEDNAME", __file__)
                return

            regex_match_sc = self.sectorcarrier_regex1.match(sector_carrier)

            if regex_match_sc is None:

                if sector_carrier in self.sc_nen_dict.keys():
                    document["CELL_NAME"] = document["NETWORKELEMENTNAME"] + self.sc_nen_dict[
                        sector_carrier]
                    document["EUTRANCELLFDD"] = document["CELL_NAME"]
                else:
                    document["CELL_NAME"] = sector_carrier
                    document["EUTRANCELLFDD"] = document["CELL_NAME"]
            else:
                regex_match_mc = self.mecontext_regex.match(mecontext)

                # EXEMPLO: document["SECTORCARRIER"] = "4" and document["MECONTEXT"] ="SRTGDDG12"
                if len(regex_match_sc.group(1)) == 0 and regex_match_mc is None:
                    document["CELL_NAME"] = document["NETWORKELEMENTNAME"] + self.sc_nen_dict2[
                        sector_carrier]
                    document["EUTRANCELLFDD"] = document["CELL_NAME"]
                # EXEMPLO: document["SECTORCARRIER"] = "TFSR14" and document["MECONTEXT"] ="TSEER21"
                elif len(regex_match_sc.group(1)) != 0 and regex_match_mc is not None:
                    document["CELL_NAME"] = document["NETWORKELEMENTNAME"] + self.sc_nen_dict3[
                        regex_match_sc.group(2)]
                    document["EUTRANCELLFDD"] = document["CELL_NAME"]
                # EXEMPLO: ALL ELSE
                else:
                    document["CELL_NAME"] = sector_carrier
                    document["EUTRANCELLFDD"] = document["CELL_NAME"]
        except KeyError as e:
            logger.warning("Column is missing from document in SECTORCARRIER treatment: {0}".format(e), __file__)

    @staticmethod
    def get_date_432(dateStr, timeZone):

        tmp_date_time = dateStr.replace("T", " ").split('+')[0]
        ts_list = re.findall(r"(\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2}):(\d{2})", tmp_date_time)
        # If the date wasn't correctly parsed, raise an error.
        if ts_list and len(ts_list[0]) >= 6:
            # Create date string with TIMESTAMP format
            tmp_date_time = "{0}-{1}-{2} {3}:{4}:{5}".format(ts_list[0][0], ts_list[0][1], ts_list[0][2], ts_list[0][3],
                                                             ts_list[0][4], ts_list[0][5])
            date_time = tmp_date_time

        # Generate date from YYYY, MM, DD, HH, mm, ss
        d = datetime(int(ts_list[0][0]), int(ts_list[0][1]), int(ts_list[0][2]), int(ts_list[0][3]), int(ts_list[0][4]),
                     int(ts_list[0][5]))
        # Subtract a number of hours equal to the time
        date_time = d - timedelta(hours=timeZone)
        date_time = str(date_time)

        return date_time

    def process_and_clear_queue_401(self, queue, baseObject={}):

        for unit_id, familyObj in queue.items():
            self.nextOp(familyObj=familyObj, baseObject=baseObject)
            self.mature_queue_401[unit_id].unitID = unit_id
            self.mature_queue_401[unit_id].clearDocuments()

    def update_queues_401(self, unitID, baseObject={}):

        # Check if incubationQueue has more than limit number of Docs
        if self.n_docs_in_cache > self.max_docs_in_incubation_cache:
            # Get oldest entry from incubation cache
            proxy_document = self.incubation_queue_401.popitem(last=False)[1]

            self.n_docs_in_cache -= 1

            # Add document to mature queue
            self.mature_queue_401[proxy_document["unitID"]].add_document_401(proxy_document["payload"])

        # Flush mature Queue if this unitID already has mature docs and if max docs is reached
        if self.mature_queue_401[unitID].nDocs > self.max_docs_in_mature_cache:
            self.process_and_clear_queue_401(self.mature_queue_401, baseObject=baseObject)

    def flush_queues_401(self, baseObject={}):

        for proxy_document in self.incubation_queue_401.values():
            self.mature_queue_401[proxy_document["unitID"]].addDocument(proxy_document["payload"])

        self.process_and_clear_queue_401(self.mature_queue_401, baseObject=baseObject)

        self.mature_queue_401 = dict()
        self.incubation_queue_401 = collections.OrderedDict()
        self.n_docs_in_cache = 0

    def add_document_401(self, unit_id, document):

        data = document["data"]

        id_key = data["MEASSTARTTIME"] + data["MEASENDTIME"] + data["NEDISTINGUISHEDNAME"] + \
                 data["MEASUREDOBJECTID"]

        # If document has already been added
        if id_key in self.incubation_queue_401:
            self.repeated_keys += 1
            # Updates corresponding document in the unit's OrderedDict
            self.incubation_queue_401[id_key]["payload"]["data"].update(document["data"])
        else:

            # Create a document that carries the actual new document, but also an indication of the unit it belongs to
            proxy_document = {
                "unitID": unit_id,
                "payload": document
            }
            # Store key and index in documents list
            self.incubation_queue_401[id_key] = proxy_document
            self.n_docs_in_cache += 1

        self.update_queues_401(unit_id)

    def treatment_401(self, filePath, familyObj=FamilyObject(), baseObject={}):

        self.flush_queues_401(baseObject=baseObject)
        self.mature_queue_401 = dict()

        # Error flag. Only valid while inside the <nPMMOResult> node where it occurs
        error = dict()
        error["value"] = False
        error["node"] = ""

        ############################################ CBT ############################################
        start_time = None
        for cbt in self.get_elements(filePath, "cbt"):
            start_time = cbt.text  # self.getDate(cbt, timeZone)

        if start_time is None:
            logger.warning(
                "No value in <cbt> node in sample. Impossible to obtain start_time \"{}\"".format(familyObj.fileName),
                __file__)

        # Iterate through all "md" nodes
        for md in self.get_elements(filePath, "md"):
            ############################################ NEID ############################################
            # Get neid from inside md
            neid = md.find(".//neid")
            ############################################ NEUN ############################################
            # Get neun from inside neid
            neun = neid.find(".//neun")
            network_element_name = self.get_node_text(neun)
            ############################################ NEDN ############################################
            # Get nedn from inside md
            nedn = md.find(".//nedn")
            ne_distinguished_name = self.get_node_text(nedn)
            if not ne_distinguished_name[1]:
                logger.warning("No value in <nedn> node in sample \"{0}\"".format(familyObj.fileName), __file__)
                continue
            ############################################ NESW ############################################
            # Get nesw from inside md
            nesw = md.find(".//nesw")
            ne_software_release = self.get_node_text(nesw)
            ############################################ MI ############################################
            # Get mi from inside md
            mi = md.find(".//mi")
            ############################################ MTS ############################################
            # Get mts from inside mi
            mts = mi.find(".//mts")
            # print mts.tag + ": " + mts.text
            meas_end_time = mts.text
            ############################################ GP ############################################
            # Get gp from inside mi
            gp = mi.find(".//gp")
            granularity_period = self.get_node_text(gp)
            # print gp.tag + ": " + gp.text

            ############################################ MT ############################################
            column_names_list_final = list()
            for mt in mi.findall(".//mt"):
                column_names_list_final.append(mt.text.upper())

            for mv in mi.findall(".//mv"):
                ############################################ MOID ############################################
                # Get moid from inside mv
                moid = mv.find(".//moid")
                try:
                    measured_object_id = self.get_node_text(moid)
                # Move to next <mv> node if moid is has no value
                except:
                    continue

                ############################################ FDN ############################################
                # fdn = ("FDN", "{0},{1}".format(neDistinguishedName[1].upper(), measuredObjectID[1].upper()))

                # Get unitID from moid string
                unit_id = moid.text.split(",")[-1].split("=")[0].upper()

                # Add unit to cache
                if unit_id not in self.mature_queue_401:
                    self.mature_queue_401[unit_id] = FamilyObject()
                    self.mature_queue_401[unit_id].unitID = unit_id
                    self.mature_queue_401[unit_id].fileName = familyObj.fileName

                ############################################ R ############################################
                values_list = list()
                for r in mv.findall(".//r"):
                    values_list.append(self.get_node_text(r))

                # Check if number of values corresponds to number of columns
                if len(column_names_list_final) != len(values_list):
                    logger.warning(
                        "Nr of <mt> nodes is different from the nr of <r> nodes \"{0}\"".format(familyObj.fileName))
                    continue
                else:

                    # Add fixedValues
                    newDocument = {
                        "MEASSTARTTIME": start_time,
                        "MEASENDTIME": meas_end_time,
                        "NEDISTINGUISHEDNAME": ne_distinguished_name,
                        "NESOFTWARERELEASE": ne_software_release,
                        "NETWORKELEMENTNAME": network_element_name,
                        "GRANULARITYPERIOD": granularity_period,
                        "MEASUREDOBJECTID": measured_object_id
                    }

                    time_zone = self.get_tz(familyObj.fileName)
                    newDocument["MEASSTARTTIME"] = self.get_date_401(newDocument["MEASSTARTTIME"], time_zone)
                    newDocument["MEASENDTIME"] = self.get_date_401(newDocument["MEASENDTIME"], time_zone)

                    # enrich the MEASUREDOBJECTTYPE with the hierarchy
                    newDocument["MEASUREDOBJECTTYPE"] = self.generate_measobjtype(newDocument["MEASUREDOBJECTID"])

                    # treat the sectocarrier family
                    if unit_id.upper() == "SECTORCARRIER":
                        self.treatment_sectorcarrier(newDocument)

                    values_list = dict(zip(column_names_list_final, values_list))

                    newDocument.update(values_list)

                    # Prepare mediation message envelope
                    try:
                        data_time = familyObj.parseEnvelopeDataTime(newDocument["MEASSTARTTIME"])
                        granularity_sec = familyObj.parseEnvelopeGranularitySec(granularity_period)
                    except ValueError as e:
                        logger.warning(
                            "Could not build mediationEnvelope due to {0}: ".format(
                                e), __file__)

                    namf_document = (
                        {"dataTime": data_time, "granularitySec": granularity_sec, "data": newDocument})

                    self.add_document_401(unit_id, namf_document)

    def process_and_clear_queue_432(self, queue, baseObject={}):

        for unit_id, familyObj in queue.items():
            self.nextOp(familyObj=familyObj, baseObject=baseObject)
            self.mature_queue_432[unit_id].unitID = unit_id
            self.mature_queue_432[unit_id].clearDocuments()

    def update_queues_432(self, unitID, baseObject={}):

        # Check if incubationQueue has more than limit number of Docs
        if self.n_docs_in_cache > self.max_docs_in_incubation_cache:
            # Get oldest entry from incubation cache
            proxy_document = self.incubation_queue_432.popitem(last=False)[1]

            self.n_docs_in_cache -= 1

            # Add document to mature queue
            self.mature_queue_432[proxy_document["unitID"]].add_document_432(proxy_document["payload"])

        # Flush mature Queue if this unitID already has mature docs and if max docs is reached
        if self.mature_queue_432[unitID].nDocs > self.max_docs_in_incubation_cache:
            self.process_and_clear_queue_432(self.mature_queue_432, baseObject=baseObject)

    def flush_queues_432(self, baseObject={}):

        for proxyDocument in self.incubation_queue_432.values():
            self.mature_queue_432[proxyDocument["unitID"]].addDocument(proxyDocument["payload"])

        self.process_and_clear_queue_432(self.mature_queue_432, baseObject=baseObject)

        self.mature_queue_432 = dict()
        self.incubation_queue_432 = collections.OrderedDict()
        self.n_docs_in_cache = 0

    def add_document_432(self, unit_id, document):

        data = document["data"]

        id_key = data["MEASSTARTTIME"] + data["MEASENDTIME"] + data["NEDISTINGUISHEDNAME"] + \
                 data["MEASUREDOBJECTID"]

        # If document has already been added
        if id_key in self.incubation_queue_432:
            self.repeated_keys += 1
            # Updates corresponding document in the unit's OrderedDict
            self.incubation_queue_432[id_key]["payload"]["data"].update(document["data"])
        else:

            # Create a document that carries the actual new document, but also an indication of the unit it belongs to
            proxy_document = {
                "unitID": unit_id,
                "payload": document
            }
            # Store key and index in documents list
            self.incubation_queue_432[id_key] = proxy_document
            self.nDocsInCache += 1

        self.update_queues_432(unit_id)

    def treatment_432(self, filePath, familyObj=FamilyObject(), baseObject={}):

        self.flush_queues_432(baseObject=baseObject)
        self.mature_queue_432 = dict()

        error = dict()
        error["value"] = False
        error["node"] = ""

        try:
            tree = ET.parse(filePath)
            root = tree.getroot()
        except:
            logger.warning("File is damaged: \"{0}\"".format(familyObj.fileName), __file__)

        namespace = self.get_node_namespace(root)

        ############################################ FILEHEADER ############################################
        ############################################ measCollec ############################################
        start_time = None
        try:
            file_header = root.find(".//{}fileHeader".format(namespace))
            ne_distinguished_name = file_header.get("dnPrefix")

            # Checks if neDistinguishedName is empty
            if len(ne_distinguished_name.strip()) == 0:
                logger.warning("dnPrefix is empty in sample \"{0}\"".format(familyObj.fileName), __file__)
            meas_collec = file_header.find(".//{}measCollec".format(namespace))
            start_time = meas_collec.get("beginTime")
        except:
            logger.warning("Error processing fileHeader node in sample \"{0}\"".format(familyObj.fileName), __file__)
            return

        # Iterate through all "measData" nodes
        for measData in self.get_elements(filePath, "measData"):
            ############################################ NEUN ############################################
            # neun does not exist in 432
            network_element_name = None
            ############################################ NESW ############################################
            # Get software version from inside measData
            managed_element = measData.find(".//{}managedElement".format(namespace))

            ne_software_release = ""

            if managed_element is not None:
                ne_software_release = managed_element.get("swVersion")
                network_element_name = managed_element.get("userLabel")

            # If not in userlabel, get the network_element_name from mecontext
            if network_element_name is None:
                nedn_match = self.nedn_regex.match(ne_distinguished_name)
                if nedn_match is not None:
                    network_element_name = nedn_match.group(1)

            ############################################ measInfo ############################################
            # Get mi from inside md
            for measInfo in measData.findall(".//{}measInfo".format(namespace)):
                id_found = False
                ############################################ granPeriod ############################################
                gran_period = measInfo.find(".//{}granPeriod".format(namespace))

                if gran_period is not None:
                    meas_end_time = gran_period.get("endTime")
                    granularity_period = gran_period.get("duration")
                else:
                    logger.warning("No <granPeriod> node in measInfo node.", __file__)
                    continue

                ############################################ measType ############################################
                # Creates dictionary by index - columnName
                columnNamesListFinal = dict()
                for measType in measInfo.findall(".//{}measType".format(namespace)):
                    columnNamesListFinal[measType.get('p')] = measType.text.upper()

                for measValue in measInfo.findall(".//{}measValue".format(namespace)):
                    ############################################ measuredObjectID ############################################
                    # Get measObjLdn from inside measValue
                    measured_object_id = measValue.get("measObjLdn")
                    newDocument = dict()

                    if measured_object_id is None:
                        continue
                    elif len(measured_object_id) == 0:
                        continue

                    if id_found is False:
                        # Get unitID from moid string
                        unitmatch = self.unitid_regex.match(measured_object_id)
                        if unitmatch is not None:
                            if unitmatch.group('unitid1') is not None:
                                unit_id = unitmatch.group('unitid1').upper()
                                id_found = True
                                # Add unit to cache
                                if unit_id not in self.mature_queue_432:
                                    self.mature_queue_432[unit_id] = FamilyObject()
                                    self.mature_queue_432[unit_id].unitID = unit_id
                                    self.mature_queue_432[unit_id].fileName = familyObj.fileName

                            elif unitmatch.group('unitid2') is not None:
                                unit_id = unitmatch.group('unitid2').upper()
                                id_found = True
                                # Add unit to cache
                                if unit_id not in self.mature_queue_432:
                                    self.mature_queue_432[unit_id] = FamilyObject()
                                    self.mature_queue_432[unit_id].unitID = unit_id
                                    self.mature_queue_432[unit_id].fileName = familyObj.fileName
                            else:
                                logger.warning("MeasValue has invalid moid: \"{0}\": {1}".format(familyObj.fileName,
                                                                                                 measured_object_id),
                                               __file__)
                                continue

                        else:
                            logger.warning(
                                "MeasValue has invalid moid: \"{0}\": {1}".format(familyObj.fileName,
                                                                                  measured_object_id), __file__)
                            continue

                    ############################################ R ############################################
                    for r in measValue.findall(".//{}r".format(namespace)):
                        index = r.get('p')
                        # Verify if index is associated to a columnName
                        if index in columnNamesListFinal:
                            newDocument[columnNamesListFinal[index]] = str(self.get_node_text(r))

                    # Creates preset columns
                    newDocument["MEASSTARTTIME"] = start_time
                    newDocument["MEASENDTIME"] = meas_end_time
                    newDocument["NEDISTINGUISHEDNAME"] = ne_distinguished_name
                    newDocument["NESOFTWARERELEASE"] = ne_software_release
                    newDocument["NETWORKELEMENTNAME"] = network_element_name
                    newDocument["GRANULARITYPERIOD"] = granularity_period.replace("PT", "").replace("S", "")
                    newDocument["MEASUREDOBJECTID"] = measured_object_id

                    time_zone = self.get_tz(familyObj.fileName)
                    newDocument["MEASSTARTTIME"] = self.get_date_432(newDocument["MEASSTARTTIME"], time_zone)
                    newDocument["MEASENDTIME"] = self.get_date_432(newDocument["MEASENDTIME"], time_zone)

                    # enrich the MEASUREDOBJECTTYPE with the hierarchy
                    newDocument["MEASUREDOBJECTTYPE"] = self.generate_measobjtype(newDocument["MEASUREDOBJECTID"])

                    # treat the sectocarrier family
                    if unit_id.upper() == "SECTORCARRIER":
                        self.treatment_sectorcarrier(newDocument)

                    # Prepare mediation message envelope
                    try:
                        data_time = familyObj.parseEnvelopeDataTime(newDocument["MEASSTARTTIME"])
                        granularity_sec = familyObj.parseEnvelopeGranularitySec(granularity_period)
                    except ValueError as e:
                        logger.warning(
                            "Could not build mediationEnvelope due to {0}: ".format(
                                e), __file__)

                    namf_document = (
                        {"dataTime": data_time, "granularitySec": granularity_sec, "data": newDocument})

                    self.add_document_432(unit_id, namf_document)

    def process(self, familyObj=FamilyObject(), baseObject={}):

        files_to_process = familyObj.getFiles()

        # Clear used information
        familyObj.clearFiles()
        familyObj.clearDocuments()

        for file_path in files_to_process:

            logger_filepath = file_path

            familyObj.fileName = os.path.basename(file_path)

            try:
                # If file is compressed, replace the file path with a gzip buffered stream
                if os.path.splitext(file_path)[1] == ".gz":
                    file_path = io.BufferedReader(gzip.open(file_path))
                    # Sligthly less efficient alternative for large files, but slightly faster for smaller files.
                    # Keep this in comment, if case circumstances change
                    # p = subprocess.Popen(["zcat", file_path], stdout=subprocess.PIPE)
                    # file_path = cStringIO.StringIO(p.communicate()[0])
            except IOError:
                logger.warning("Could not open sample file \"{}\" in read mode: ".format(logger_filepath), __file__)
                continue

            logger.debug(
                "Reading Ericsson Performance 3GPP 32.XXX XML files '{0}' contents...".format(os.path.basename(logger_filepath)),__file__)

            try:
                tree = ET.parse(file_path)
                root = tree.getroot()
                format_file = root.tag
                self.rewindFile(file_path)
            except Exception as e:
                print e
                logger.warning("File is damaged: \"{0}\"".format(logger_filepath), __file__)
                continue

            if format_file == "mdc":
                self.treatment_401(file_path, familyObj, baseObject)
                self.flush_queues_401(baseObject=baseObject)
            else:
                self.treatment_432(file_path, familyObj, baseObject)
                self.flush_queues_432(baseObject=baseObject)
