__doc__ = \
    '''
    Ericsson 3GPP 32.401 XML reader

    Spec file syntax:
    <operation type="Readers" name="ERICSSON.3GPP.32_401.DTD" consolidation="True"/>


    Sample:
    <?xml version="1.0"?>
    <?xml-stylesheet type="text/xsl" href="MeasDataCollection.xsl"?>
    <!DOCTYPE mdc SYSTEM 'MeasDataCollection.dtd'>
    <mdc xmlns:HTML="http://www.w3.org/TR/REC-xml">
        <mfh>
            <ffv>32.401 V6.2</ffv>
            <sn>SubNetwork=ONRM_ROOT_MO_R,SubNetwork=RNC01PAE,MeContext=RNC01PAE</sn>
            <st/>
            <vn/>
            <cbt>20200518154500Z</cbt>
        </mfh>
        <md>
            <neid>
                <neun>RNC01PAE</neun>
                <nedn>SubNetwork=ONRM_ROOT_MO_R,SubNetwork=RNC01PAE,MeContext=RNC01PAE</nedn>
                <nesw>CXP9021776/2_R4LA16</nesw>
            </neid>
            <mi>
                <mts>20200518160000Z</mts>
                <gp>900</gp>
                <mt>pmVcBbe</mt>
                <mv>
                    <moid>ManagedElement=1,Equipment=1,Subrack=MS,Slot=27,PlugInUnit=1,ExchangeTerminal=1,Os155SpiTtp=pp1,Vc4Ttp=1</moid>
                    <r>0</r>
                </mv>
                <mv>
                    <moid>ManagedElement=1,Equipment=1,Subrack=MS,Slot=27,PlugInUnit=1,ExchangeTerminal=1,Os155SpiTtp=pp2,Vc4Ttp=1</moid>
                    <r>0</r>

                </mv>
            </mi>
        </md>
        <md>
        ...
        </md>
'''

__version__ = '1.0'

__authors__ = [
    "Version 1.0: Joao Pio <joao-t-pio@alticelabs.com>"
]

# Native libraries
import importlib
import collections
import xml.etree.cElementTree as ET
import os
import re
import gzip
import cStringIO
import io
from datetime import datetime, timedelta

# Local libraries
BaseOperator = importlib.import_module("shelf.collectorprocess.operators.BaseOperator").BaseOperator
FamilyObject = importlib.import_module("shelf.collectorprocess.operators.FamilyObject").FamilyObject
logger = importlib.import_module("shelf.collectorprocess.logger").logger


class Operator(BaseOperator):

    # Class Constructor
    def __init__(self, operationParams, baseObject={}):
        BaseOperator.__init__(self, operationParams, baseObject=baseObject)

        self._incubation_queue = collections.OrderedDict()
        self._mature_queue = dict()
        self._max_docs_in_incubation_cache = 100000
        self._max_docs_in_mature_cache = 1000

        self._unit_source = 'moid'  # self.options["unitsource"]

        self._n_docs_in_cache = 0
        self.repeated_keys = 0

        # Initialize consolidation flag according to spec file
        self.consolidation = False
        if "consolidation" in self.options:
            if self.options["consolidation"].upper() == "TRUE":
                self.consolidation = True

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
    def mature_queue(self):
        return self._mature_queue

    @mature_queue.setter
    def mature_queue(self, value):
        self._mature_queue = value

    @property
    def n_docs_in_cache(self):
        return self._n_docs_in_cache

    @n_docs_in_cache.setter
    def n_docs_in_cache(self, value):
        self._n_docs_in_cache = value

    @property
    def incubation_queue(self):
        return self._incubation_queue

    @incubation_queue.setter
    def incubation_queue(self, value):
        self._incubation_queue = value

    @property
    def max_docs_in_incubation_cache(self):
        return self._max_docs_in_incubation_cache

    @max_docs_in_incubation_cache.setter
    def max_docs_in_incubation_cache(self, value):
        self._max_docs_in_incubation_cache = value

    @staticmethod
    def get_elements(filename_or_file, tag):
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

    # Rewinds a buffered reader, does nothing if not a buffered reader
    @staticmethod
    def rewind(buffered_reader):
        if isinstance(buffered_reader, (io.BufferedReader, cStringIO.InputType)):
            try:
                buffered_reader.seek(0)
            except AttributeError as e:
                logger.error("Could not rewind the unzipped stream of due to {0}".format(e.message))

        return

    def process_and_clear_queue(self, queue, baseObject={}):

        for unitID, familyObj in queue.items():

            logger.debug("[Reader] Calling next nextOp with {0} documents in hand ...".format(len(familyObj.documents)))
            self.nextOp(familyObj=familyObj, baseObject=baseObject)

            self.mature_queue[unitID].unitID = unitID
            self.mature_queue[unitID].clearDocuments()

    def update_queues(self, unitID, baseObject={}):

        # Check if incubation_queue has more than limit number of Docs
        if self.n_docs_in_cache > self.max_docs_in_incubation_cache:
            # Get oldest entry from incubation cache
            proxyDocument = self.incubation_queue.popitem(last=False)[1]

            self.n_docs_in_cache -= 1

            # Add document to mature queue
            self.mature_queue[proxyDocument["unitID"]].addDocument(proxyDocument["payload"])

        # Flush mature Queue if this unitID already has mature docs and if max docs is reached
        if self.mature_queue[unitID].nDocs > self.max_docs_in_mature_cache:
            self.process_and_clear_queue(self.mature_queue, baseObject=baseObject)

    def flush_queues(self, baseObject={}):

        for proxyDocument in self.incubation_queue.values():
            self.mature_queue[proxyDocument["unitID"]].addDocument(proxyDocument["payload"])

        self.process_and_clear_queue(self.mature_queue, baseObject=baseObject)

        self.mature_queue = dict()
        self.incubation_queue = collections.OrderedDict()
        self.n_docs_in_cache = 0

    def add_document(self, unitID, document, familyObj, baseObject={}):

        if self.consolidation:
            data = document["data"]

            id_key = data["MEASSTARTTIME"] + data["NEDISTINGUISHEDNAME"] + data["MEASUREDOBJECTID"]

            # If document has already been added
            if id_key in self.incubation_queue:
                self.repeated_keys += 1
                # Updates corresponding document in the unit's OrderedDict
                self.incubation_queue[id_key]["payload"]["data"].update(document["data"])
            else:

                # Create a document that carries the actual new document, but also an indication of the unit it belongs to
                proxy_document = {
                    "unitID": unitID,
                    "payload": document
                }
                # Store key and index in documents list
                self.incubation_queue[id_key] = proxy_document
                self.n_docs_in_cache += 1

            self.update_queues(unitID)
        else:
            familyObj.setUnitID(unitID)
            familyObj.addDocument(document)
            self.nextOp(familyObj=familyObj, baseObject=baseObject)

    @staticmethod
    def get_node_text(node):
        if not node.text:
            node.text = ""
        else:
            node.text = node.text.strip()

        return node.text

    @staticmethod
    def get_tz(file_name):
        # Base timeZone if another one cannot be calculated from the fileName
        time_zone = "0000"

        # fileName Ex: A20131014.0000-0300-0015-0300_SubNetwork=ONRM_ROOT_MO,SubNetwork=RNCCTA1,MeContext=RNCCTA1_statsfile.xml
        if "_" in file_name:
            tmp_tz = file_name.split("_")[0]

            # tmpTZ Ex: A20131014.0000-0300-0015-0300
            if "." in tmp_tz:
                tmp_tz = tmp_tz.split(".")[-1]

                # tmpTZ Ex: 0015-0300-0030-0300
                if "-" in tmp_tz:
                    tmp_tz = tmp_tz.split("-")

                    # tmpTZ Ex: ["0015", "0300", "0030", "0300"]
                    if len(tmp_tz) == 4:
                        time_zone = tmp_tz[-1]

        # Converts timeZone from string to integer
        try:
            time_zone = time_zone.rstrip("0")
            time_zone = int(time_zone)
        except:
            time_zone = 0

        return time_zone

    @staticmethod
    def get_date(date_str, time_zone):

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

    def process(self, familyObj=FamilyObject(), baseObject={}):

        logger.debug("[Reader] Reading Ericsson Performance XML files' contents...")

        files_to_process = familyObj.getFiles()
        familyObj.clearFiles()
        # Process each file
        for file_path in files_to_process:

            try:
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

                self.flush_queues(baseObject=baseObject)
                self.mature_queue = dict()

                # Error flag. Only valid while inside the <nPMMOResult> node where it occurs
                error = dict()
                error["value"] = False
                error["node"] = ""

                ############################################ CBT ############################################
                start_time = None
                for cbt in self.get_elements(file_path, "cbt"):
                    start_time = cbt.text  # self.getDate(cbt, timeZone)

                if start_time is None:
                    logger.warning(
                        "No value in <cbt> node in sample. Impossible obtain startTime \"{}\"".format(
                            familyObj.fileName))

                # Iterate through all "md" nodes
                self.rewind(file_path)
                for md in self.get_elements(file_path, "md"):
                    # ########################################### NEID ############################################
                    # Get neid from inside md
                    neid = md.find(".//neid")
                    # ########################################### NEUN ############################################
                    # Get neun from inside neid
                    neun = neid.find(".//neun")
                    network_element_name = self.get_node_text(neun)
                    # ########################################### NEDN ############################################
                    # Get nedn from inside md
                    nedn = md.find(".//nedn")
                    ne_distinguished_name = self.get_node_text(nedn)
                    if not ne_distinguished_name[1]:
                        logger.warning("No value in <nedn> node in sample \"{}\"".format(familyObj.fileName))
                        continue
                    # ########################################### NESW ############################################
                    # Get nesw from inside md
                    nesw = md.find(".//nesw")
                    ne_software_release = self.get_node_text(nesw)
                    # ########################################### MI ############################################
                    # Get mi from inside md
                    mi = md.find(".//mi")
                    # ########################################### MTS ############################################
                    # Get mts from inside mi
                    mts = mi.find(".//mts")
                    meas_end_time = mts.text
                    # ########################################### GP ############################################
                    # Get gp from inside mi
                    gp = mi.find(".//gp")
                    granularity_period = self.get_node_text(gp)

                    # ########################################### MT ############################################
                    column_names_list_final = list()
                    for mt in mi.findall(".//mt"):
                        column_names_list_final.append(mt.text.upper())

                    for mv in mi.findall(".//mv"):
                        # ########################################### MOID ############################################
                        # Get moid from inside mv
                        moid = mv.find(".//moid")
                        try:
                            measured_object_id = self.get_node_text(moid)
                        # Move to next <mv> node if moid is has no value
                        except:
                            continue

                        # ########################################### FDN ############################################
                        # fdn = ("FDN", "{0},{1}".format(neDistinguishedName[1].upper(), measuredObjectID[1].upper()))

                        # Get unitID from moid string
                        unit_id = moid.text.split(",")[-1].split("=")[0].upper()

                        # Add unit to cache
                        if unit_id not in self.mature_queue:
                            self.mature_queue[unit_id] = FamilyObject()
                            self.mature_queue[unit_id].unitID = unit_id
                            self.mature_queue[unit_id].fileName = familyObj.fileName

                        # ########################################### R ############################################
                        values_list = list()
                        for r in mv.findall(".//r"):
                            values_list.append(self.get_node_text(r))

                        # Check if number of values corresponds to number of columns
                        if len(column_names_list_final) != len(values_list):
                            logger.warning(
                                "Nr of <mt> nodes is different from the nr of <r> nodes \"{0}\"".format(
                                    familyObj.fileName))
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
                            newDocument["MEASSTARTTIME"] = self.get_date(newDocument["MEASSTARTTIME"], time_zone)
                            newDocument["MEASENDTIME"] = self.get_date(newDocument["MEASENDTIME"], time_zone)

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

                            self.add_document(unit_id, namf_document, familyObj)

                self.flush_queues(baseObject=baseObject)
            except Exception as e:
                logger.warning("File \"{0}\" is damaged due to: {1}".format(familyObj.fileName, e))
                continue
