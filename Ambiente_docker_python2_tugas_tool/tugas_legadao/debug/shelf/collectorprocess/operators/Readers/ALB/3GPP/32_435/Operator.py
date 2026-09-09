#!/usr/bin/env python

__doc__ = \
    '''
    AlticeLabs 3GPP 32.435 Performance XML reader

    Spec file syntax:
    <operation type="Readers" name="ALB.3GPP.32_435" use_end_time="True" lower_end_time="True" process_me="False" minfo_optionals="False" jump_mtypes="True" intervalUnit="H/M/S" />
'''

__version__ = '1.2'

__authors__ = [
                "Version 0.1: Francisco Santiago <francisco-j-santiago@telecom.pt>"
                "Version 1.2: Joao Pio <joao-t-pio@alticelabs.com>"
                "Version 1.1: Bruno Silva <bruno-e-silva@alticelabs.com>"
            ]

# Native libraries
import xml.etree.cElementTree as ET
import os
import gzip
import cStringIO
from datetime import timedelta, datetime
import io
import re
import importlib

# Local libraries
BaseOperator = importlib.import_module("shelf.collectorprocess.operators.BaseOperator").BaseOperator
FamilyObject = importlib.import_module("shelf.collectorprocess.operators.FamilyObject").FamilyObject
logger = importlib.import_module("shelf.collectorprocess.logger").logger


# Rewinds a buffered reader, does nothing if not a buffered reader
def rewind(buffered_reader):
    if isinstance(buffered_reader, (io.BufferedReader, cStringIO.InputType)):
        try:
            buffered_reader.seek(0)
        except AttributeError as e:
            logger.error("Could not rewind the unzipped stream of due to {0}".format(e.message))

    return


def getelements(filename_or_file, tag):
    context = iter(ET.iterparse(filename_or_file, events=('start', 'end')))
    # get root element
    _, root = next(context)

    if isinstance(tag, list):
        multi = True
    else:
        multi = False

    namespace = None
    for event, elem in context:
        if event == 'start' and namespace is None:
            if "}" in elem.tag:
                namespace = elem.tag.split("}")[0].strip("{")
                namespace = "{" + namespace + "}"
            else:
                namespace = ""

        if multi:
            for t in tag:
                if event == 'end' and elem.tag == namespace + t:
                    yield elem, namespace
                    # preserve memory
                    elem.clear()
        else:
            if event == 'end' and elem.tag == namespace + tag:
                    yield elem, namespace
                    # preserve memory
                    elem.clear()


class Operator(BaseOperator):

    # Class Constructor
    def __init__(self, operationParams, baseObject={}):
        BaseOperator.__init__(self, operationParams, baseObject=baseObject)

        self.datetime_regex = re.compile(r'^(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}).*$')

        # Initialize end time and gp cache
        self.time_cache = dict()

        # Initialize start time calculator flag according to spec file
        self.use_end_time = False
        if "use_end_time" in self.options:
            if self.options["use_end_time"].upper() == "TRUE":
                self.use_end_time = True

        # Initialize start time calculator flag according to spec file
        self.lower_end_time = False
        if "lower_end_time" in self.options:
            if self.options["lower_end_time"].upper() == "TRUE":
                self.lower_end_time = True

        # Initialize managed element process flag according to spec file
        self.process_managed_element = False
        if "process_me" in self.options:
            if self.options["process_me"].upper() == "TRUE":
                self.process_managed_element = True

        # Initialize meas info optional fields process flag according to spec file
        self.process_meas_info_optionals = False
        if "minfo_optionals" in self.options:
            if self.options["minfo_optionals"].upper() == "TRUE":
                self.process_meas_info_optionals = True

        # Initialize empty meas types reaction flag according to spec file
        self.jump_empty_mtypes = False
        if "jump_mtypes" in self.options:
            if self.options["jump_mtypes"].upper() == "TRUE":
                self.jump_empty_mtypes = True

        # Sets the interval unit, as default its defined to Minutes
        self.intervalUnit = 'M'
        if "intervalUnit" in self.options:
            self.intervalUnit = self.options["intervalUnit"].upper()

    def convert(self, familyObj=FamilyObject()):

        for document in familyObj.getDocuments():

            if "BEGINTIME" in document["data"].keys():
                start_time_match = self.datetime_regex.match(document["data"]["BEGINTIME"])
                if start_time_match is not None:
                    start_time_datetime = datetime.strptime(start_time_match.group(1), "%Y-%m-%dT%H:%M:%S")
                    document["data"]["BEGINTIME"] = start_time_datetime.isoformat(sep=" ")
                else:
                    logger.error(
                        "Could not convert start time due to non matching regex with {0} ".format(document["data"]["BEGINTIME"]), __file__)
                    continue

            if "ENDTIME" in document["data"].keys():
                # Extract end time, remove timezone and turn it into a datetime object
                end_time_match = self.datetime_regex.match(document["data"]["ENDTIME"])
                if end_time_match is not None:
                    end_time_datetime = datetime.strptime(end_time_match.group(1), "%Y-%m-%dT%H:%M:%S")
                    document["data"]["ENDTIME"] = end_time_datetime.isoformat(sep=" ")
                else:
                    logger.error(
                        "Could not convert end time due to non matching regex with {0}: ".format(document["data"]["ENDTIME"]), __file__)
                    continue

    def is_endtime_lower(self, end_time, filefooter_end_time):
        try:
            endtime = datetime.strptime(end_time, "%Y-%m-%dT%H:%M:%S.%fZ")
            ff_endtime = datetime.strptime(filefooter_end_time, "%Y-%m-%dT%H:%M:%S.%fZ")
        except Exception:
            raise ET.ParseError(
                "Sample file does not conform to 32.435 standard due to wrong format of endTime/fileFooter endTime")

        return endtime < ff_endtime

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
                "Reading Altice Labs Performance 3GPP 32.435 XML files '{0}' contents...".format(os.path.basename(logger_filepath)),
                __file__)
            try:
                # Nodes to request on the first run of the file
                nodes_request = ["fileHeader", "fileFooter"]

                if self.process_managed_element:
                    nodes_request.append("managedElement")

                # Obtaining header/footer and optionally managed element in the same getelements call, gives a 10% performance gain
                for node, namespace in getelements(file_path, nodes_request):

                    if "fileHeader" in node.tag:
                        try:
                            # Mandatory field
                            file_format_version = node.attrib["fileFormatVersion"]
                        except KeyError:
                            raise ET.ParseError("Sample file does not conform to 32.435 standard due to lack of fileFormatVersion in fileHeader")

                        # Optional fields
                        vendor_name = node.get("vendorName")
                        dn_prefix = node.get("dnPrefix")

                        for meas_collec in node.iter(namespace + "measCollec"):
                            try:
                                # Mandatory Field
                                begin_time = meas_collec.attrib["beginTime"]
                            except KeyError:
                                raise ET.ParseError("Sample file does not conform to 32.435 standard due to lack of beginTime in measCollec")

                        for file_sender in node.iter(namespace + "fileSender"):
                            # Optional fields
                            fh_local_dn = file_sender.get("localDn")
                            element_type = file_sender.get("elementType")

                    # Process managed element only if requested in spec file (10% performance gain)
                    elif "managedElement" in node.tag:
                        # Optional fields
                        me_local_dn = node.get("localDn")
                        user_label = node.get("userLabel")
                        sw_version = node.get("swVersion")

                    elif "fileFooter" in node.tag:
                        for meas_collec in node.iter(namespace + "measCollec"):
                            try:
                                # Mandatory Field
                                filefooter_end_time = meas_collec.attrib["endTime"]
                            except KeyError:
                                raise ET.ParseError(
                                    "Sample file does not conform to 32.435 standard due to lack of endTime in fileFooter")

                # Rewind if we're dealing with a Buffered Reader or a cStringIO
                rewind(file_path)

                for meas_info, namespace in getelements(file_path, "measInfo"):

                    try:
                        unit_id = meas_info.attrib["measInfoId"].upper()
                    except KeyError:
                        raise ET.ParseError(
                            "Sample file lacks measInfoId of measInfo. Can't identify unit id.")

                    # Optional nodes in 32.435 - Deactivation causes an inscrease in performance of 5%
                    if self.process_meas_info_optionals:
                        for job in meas_info.iter(namespace + "job"):
                            try:
                                job_id = job.attrib["jobId"]
                            except KeyError:
                                raise ET.ParseError("Sample file does not conform to 32.435 standard due to lack of jobId in job")

                        for rep_period in meas_info.iter(namespace + "repPeriod"):
                            try:
                                rep_duration = rep_period.attrib["duration"]
                            except KeyError:
                                raise ET.ParseError("Sample file does not conform to 32.435 standard due to lack of duration in repPeriod")

                    granularity_period = ""
                    for gran_period in meas_info.iter(namespace + "granPeriod"):
                        try:
                            granularity_period = gran_period.attrib["duration"]
                            end_time = gran_period.attrib["endTime"]
                        except KeyError:
                            raise ET.ParseError("Sample file does not conform to 32.435 standard due to lack of duration/endTime in granPeriod")

                    if self.lower_end_time:
                        if not self.is_endtime_lower(end_time, filefooter_end_time):
                            continue

                    try:
                        granularity_sec = self.format_interval(int(FamilyObject.parseEnvelopeGranularitySec(granularity_period)), granularity_period[-1:].upper(), 'S')
                    except ValueError as e:
                        logger.error(
                            "Could not calculate granularity period due to {0}: ".format(
                                e), __file__)
                        continue

                    # Check if begin time is calculated through a delta or not
                    if self.use_end_time:
                        # Check if end time and gp are already in the cache
                        if "{0}{1}".format(granularity_period, end_time) in self.time_cache:
                            begin_time = self.time_cache["{0}{1}".format(granularity_period, end_time)]
                        else:
                            # Convert granularity period into a timedelta
                            granularity_as_delta = timedelta(0, int(granularity_sec))

                            # Extract end time, remove timezone and turn it into a datetime object
                            end_time_match = self.datetime_regex.match(end_time)
                            if end_time_match is not None:
                                end_time_datetime = datetime.strptime(end_time_match.group(1), "%Y-%m-%dT%H:%M:%S")
                                # Subtract the gp delta to the end time object and return it as a string to start time
                                begin_time = (end_time_datetime - granularity_as_delta).isoformat(sep="T")
                                # Update cache
                                self.time_cache["{0}{1}".format(granularity_period, end_time)] = begin_time
                            else:
                                logger.error(
                                    "Could not parse end time due to non matching regex with {0}: ".format(end_time), __file__)
                                continue

                    else:
                        # Behaviour by default
                        end_time = filefooter_end_time

                    item_names = dict()
                    item_values = dict()

                    try:
                        # File format has the measTypes style node (all counters in same node):
                        # <measTypes> m2002c0003 m2002c0004 m2002c0005 m2002c0007 </measTypes>
                        meas_types = meas_info.iter(namespace + "measTypes").next()

                        try:
                            for n, name in enumerate(meas_types.text.split(" ")):
                                # Dont insert empty names
                                if name != "":
                                    item_names[n+1] = name.upper()
                        except AttributeError:
                            # Empty measTypes node: <measTypes></measTypes>
                            if self.jump_empty_mtypes:
                                # Jump the whole file, in case the spec has that setting - Can not prove that it has any significant increase in performance
                                break
                            else:
                                # Jump a line to the next measInfo
                                continue

                    except StopIteration as e:
                        # If one single iteration raises a StopIteration, this node is not present. Must be measType instead:
                        # <measType>m2002c0003</measType>
                        # <measType>m2002c0004</measType>
                        # <measType>m2002c0005</measType>
                        # <measType>m2002c0007</measType>

                        for n, meas_type in enumerate(meas_info.iter(namespace + "measType")):
                            # Check for existence of optional positioning attribute
                            # <measType p="1">m2002c0003</measType>
                            p = meas_type.get("p")
                            if p is None:
                                item_names[n+1] = meas_type.text.upper()
                            else:
                                item_names[int(p)] = meas_type.text.upper()

                    for meas_value in meas_info.iter(namespace + "measValue"):
                        measobjldn = meas_value.attrib["measObjLdn"]

                        # Resets familyObj values to accomodate new unit's data
                        familyObj.setUnitID(unit_id)
                        familyObj.clearDocuments()

                        try:
                            # File format has the measResults style node (all counters in same node):
                            # <measResults> 234 12 2 0 </measResults>
                            meas_results = meas_value.iter(namespace + "measResults").next()

                            try:
                                for n, value in enumerate(meas_results.text.split(" ")):
                                    # Dont insert empty names
                                    if value == "":
                                        continue
                                    elif value.upper() == "NIL":
                                        # NIL strings are to be replaced with empty string
                                        item_values[n+1] = ""
                                    else:
                                        item_values[n+1] = value
                            except AttributeError:
                                # Empty measResults node: <measResults></measResults>
                                pass

                        except StopIteration as e:
                            # If one single iteration raises a StopIteration, this node is not present. Must be r instead:
                            # <r>23</r>
                            # <r>23222</r>
                            # <r>0</r>
                            # <r>676</r>

                            for n, r in enumerate(meas_value.iter(namespace + "r")):
                                # Check for existence of optional positioning attribute
                                # <r p="1">1</r>
                                p = r.get("p")
                                if p is None:
                                    item_values[n+1] = r.text
                                else:
                                    item_values[int(p)] = r.text

                        document = dict()

                        for key in item_names.keys():
                            try:
                                document[item_names[key]] = item_values[key]
                            except KeyError:
                                continue

                        document["MEASOBJLDN"] = measobjldn

                        document["BEGINTIME"] = begin_time
                        document["ENDTIME"] = end_time
                        document["DURATION"] = granularity_period

                        try:
                            document["INTERVAL"] = self.format_interval(granularity_sec, 'S', self.intervalUnit)
                        except ValueError as e:
                            document["INTERVAL"] = granularity_sec
                            logger.warning(
                                "Could not calculate granularity period due to {0}: ".format(
                                    e), __file__)

                        document["VENDORNAME"] = vendor_name
                        document["DNPREFIX"] = dn_prefix
                        document["LOCALDN"] = fh_local_dn
                        document["ELEMENTTYPE"] = element_type

                        if self.process_managed_element:
                            document["LOCALDN"] = me_local_dn
                            document["USERLABEL"] = user_label
                            document["SWVERSION"] = sw_version
                        if self.process_meas_info_optionals:
                            document["JOBID"] = job_id
                            document["DURATION"] = rep_duration

                        # Prepare Namf Mediation envelope
                        try:
                            data_time = FamilyObject.parseEnvelopeDataTime(begin_time)
                        except ValueError as e:
                            logger.warning(
                                "Could not build mediationEnvelope due to : {0}".format(
                                    e), __file__)
                            continue

                        data_document = {"dataTime": data_time, "granularitySec": granularity_sec, "data": document}

                        familyObj.addDocument(data_document)

                        self.convert(familyObj=familyObj)
                        self.nextOp(familyObj=familyObj, baseObject=baseObject)

            except ET.ParseError as e:
                logger.error("Malformed Altice Labs 3GPP XML file '{0}', due to {1}".format(os.path.basename(logger_filepath), e.message),__file__)

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
