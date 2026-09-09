__doc__ = \
    __version__ = '0.1'
__authors__ = [
    'Version 0.2: Gil Martins <gil-l-martins@alticelabs.com>'
]

import re
from lib.objects.column import column
from lib.objects.hierarchy import hierarchy
from lib.functions import *
import xml.etree.ElementTree as ET


# Example use-cases:
# RACK=(#),SHELF=1(#),SLOT=(#),PORT=(#),ONU=(#),GPON ONU Ethernet Port=(#)
# ?,HNBId=?,Fsn=?,bSRName=?,manualPscUsed=?,OpMode=?
# SubNetwork_1=?,SubNetwork_2=?,SubNetwork_3=?,SubNetwork_4=?,ManagedElement=?,bsrFunction=?
# ?/ATS MODULE:Module number=?, Module type=?/ATS MOUDLE:?
# ?/ATS:ATS ID=?/ATSCXSG:Group ID=?, Sub-group ID=?


# NOTES @ multipleFieldsGeneric  <To use multiple fields : verify inputFormat:nokiaBaseDoc_V2's way of handling 'extra'>:
# > Rule prepared to deal with the regular string for one hierarchy field, but also for more than one, if info is provided correctly in 'unitobj.extra':
# -- if additional info is provided in 'unitobj.extra' that matches a given 'fieldName' -> operation will be applied on given info, to that field
# -- if no 'fieldName' is provided, it is assumed that only 1 'measuredobject' operation is required and provided in the regular way: 'unitobj.measuredobject'
# -- if no 'extra' info is provided, but fieldName is, same assumption, but operation applied to given 'fieldName'


def process(unitDict, config):

    for ossId in unitDict.keys():
        unitObj = unitDict[ossId]
        fieldName = None

        # if fieldName in config
        try:
            fieldName = str(config['fieldName'])
            measured_obj = unitObj.extra[fieldName]
            measured_obj = re.sub(config['regex'], '', measured_obj)
            del unitObj.extra[config['fieldName']]

        except KeyError:
            measured_obj = re.sub(config['regex'], '', unitObj.measuredObject)

        if measured_obj == '':
            continue

        objects_list = []
        objects_tags = {}

        # IF STRING 'unitObj.measuredObjects' CONTAINS MORE THAN ONE SRING TO BREAK FOR THE SAME fieldName
        # NOTE: characters on this split-list might need changing depending on use-case.
        measured_obj_list = re.split(r'\r|\n|;|#', measured_obj)

        # GIVE CONFIG VALUES TO VARS FOR EASIER HANDLE
        #   - interChar -> separates tag/variable groups. assumed csv-like ',' by default.
        #   - sepCharDoc -> defines a variable at every instance. assumed '?' by default.
        #   - sepCharPattern -> defines the tag/variable separator. assumed '=' by default.
        #   - blockInRegex -> adds the provided symbols to pattern as a stopper to add extra protection to regex.

        try:
            inter_char = config['interChar']
        except KeyError:
            inter_char = ','

        try:
            sep_char_doc = config['sepCharDoc']
        except KeyError:
            sep_char_doc = '?'

        try:
            sep_char_pattern = config['sepCharPattern']
        except KeyError:
            sep_char_pattern = '='
        
        try:
            block_in_regex = config['blockInRegex']
        except KeyError:
            block_in_regex = ''

        # CHECK FOR STARTFIELD AND CONFIGURE
        startField = None
        has_startField = False
        if 'startField' in config and config['startField'] != '':
            startField = str(config['startField'])
            objects_list.append(startField)
            objects_tags[startField] = startField.replace(" ", "").upper()
            has_startField = True

        for base_obj in measured_obj_list:

            pre_obj_text = base_obj.split(sep_char_doc)

            measured_obj = re.sub(r',\s|/\s', ',', base_obj)
            measured_obj_items = (re.sub(r'[/|,| ]', '', measured_obj)).strip().split(sep_char_doc)

            # CLEAR '' FIELDS
            measured_obj_items = [item for item in measured_obj_items if item != '']
            pre_obj_text = [item for item in pre_obj_text if item != '']

            # IF 'startField' SUPPOUSED TO EXIST, VARIABLE-CHAR WOULD BE FIRST IN STRING:
            if base_obj[0:len(sep_char_doc)] == sep_char_doc:
                pre_obj_text.insert(0, '')
                # SAFE-MEASURE - SHOULD HAVE A STARTFIELD, DEFINES BY DEFAULT IF NONE DEFINED
                if startField is None:
                    startField = 'STARTFIELD'
                    objects_list.append(startField)
                    objects_tags[startField] = startField
                    has_startField = True

            for obj in measured_obj_items:
                # NOTE: SPLIT BY ':' MIGHT NEED CHANGING IN SOME USE-CASES
                obj = obj.split(sep_char_pattern)[0]
                # obj_id_list = (re.sub('\.|=|_|-|\(|\)|\+', '', obj)).split(':')  # clean "pre-group" tags for id definition
                obj_id_list = (re.sub('\.|=|-|\(|\)|\+', '', obj)).split(':')  # clean "pre-group" tags for id definition

                # VALIDATIONS
                if obj_id_list[-1] == '':
                    del obj_id_list[-1]

                object_id = obj_id_list[-1]

                for key in obj_id_list[:-2]:
                    if key != obj_id_list[-2]:
                        object_id = ('{0}{1}').format(key, object_id)

                objects_list.append(object_id)
                objects_tags[object_id] = object_id.replace(" ", "").upper()

            # BUILD PATTERN ############################################################################################

            pattern = '^'
            obj_counter = 0

            # HIERARCHY DEFINITION (working with ET and hierarchy() due to fieldName possibility)
            #   - if fieldName is provided -> operation style used
            #   - if no fieldName is provided -> hierarchy style used

            newHierarchy = hierarchy()
            newHierarchy.create('', [])

            operation = ET.Element("operation")
            operation.set("type", "applyRegex")
            op_regex = ET.SubElement(operation, "regex")
            # op_regex.set("pattern", pattern)

            for info in pre_obj_text:

                obj = objects_list[obj_counter]
                obj_id = objects_tags[obj]
                obj_counter += 1

                if has_startField:
                    has_startField = False  # set false for rest of pattern to add 'sep_char_pattern' to 'info'
                    pattern += info + ('(?P<' + obj_id + '>[^' + block_in_regex + ']*?)' if block_in_regex != '' else '(?P<' + obj_id + '>.*?)')
                else:

                    info_fix = info.split(sep_char_pattern)[0]  # FIX WEIRD STRING SUCH AS 'SHELF=1(#)'
                    if info_fix != info:
                        pattern += info_fix + sep_char_pattern + ('(?P<' + obj_id + '>[^' + block_in_regex + ']*?)' if block_in_regex != '' else '(?P<' + obj_id + '>.*?)')
                    else:
                        pattern += info + ('(?P<' + obj_id + '>[^' + block_in_regex + ']*?)' if block_in_regex != '' else '(?P<' + obj_id + '>.*?)')

                # SET HIERARCHY PARAMS
                newField = column()
                newField.create(obj_id, obj, validateUdn(obj), validateSqlName(obj), obj, 'ID', 'VARCHAR2(256)', 'STRING', 'STRING', '', '')
                unitObj.addAttribute(obj_id, newField)
                newHierarchy.addNewField(obj_id)
                op_new_field = ET.SubElement(op_regex, "newField")
                op_new_field.text = obj_id

            pattern += '$'

            # SET FINAL HIERARCHY PARAMS
            newHierarchy.pattern = pattern
            op_regex.set("pattern", pattern)

            if fieldName is not None and not '':
                unitObj.addOperation('item', fieldName, operation)
            else:
                unitObj.addHierarchy(pattern, newHierarchy)
