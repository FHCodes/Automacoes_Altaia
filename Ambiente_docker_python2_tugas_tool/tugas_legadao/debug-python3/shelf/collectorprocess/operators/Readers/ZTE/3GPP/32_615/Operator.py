#!/usr/bin/env python
__doc__ = '''
    ZTE Parameters 3GPP 32.615 XML reader
    Processes XML files from ZTE(NR, LTE, PLAT)
'''

__version__ = '1.0'
__authors__ = [
    "Version 0.1: Rafael Sandes <rafael-s-neiva@openlabs.com.br>",
    "Version 0.2: Felipe Henriques <felipe-s-henriques@openlabs.com.br>"
]

import lxml.etree as etree
import os
import re
import importlib
import copy
from datetime import datetime
from collections import defaultdict

BaseOperator = importlib.import_module("shelf.collectorprocess.operators.BaseOperator").BaseOperator
FamilyObject = importlib.import_module("shelf.collectorprocess.operators.FamilyObject").FamilyObject
logger = importlib.import_module("shelf.collectorprocess.logger").logger

class Operator(BaseOperator):
    """
    ZTE XML Operator for processing 3GPP 32.615 XML files
    """
    # Class Constructor
    def __init__(self, operationParams, baseObject={}, standard_mos=[]):
        BaseOperator.__init__(self, operationParams, baseObject=baseObject)
        logger.info("Initializing ZTE CM Reader Operator", __file__)
        self.standard_mos = standard_mos

    def _ensure_ascii(self, value):
        # NOTE (py2->py3): in Python 2 this returned an ASCII-encoded
        # bytestring (str/bytes were the same type there). In Python 3,
        # str is already unicode, so we now return a plain ASCII-safe
        # `str` instead of `bytes` -- returning bytes here would break
        # every caller that does string formatting/concatenation on the
        # result (they would get "b'...'" instead of the value).
        if value is None:
            return ''
        try:
            if isinstance(value, str):
                return value.encode('ascii', 'replace').decode('ascii')
            elif isinstance(value, bytes):
                return value.decode('utf-8', 'replace').encode('ascii', 'replace').decode('ascii')
            else:
                return str(value).encode('ascii', 'replace').decode('ascii')
        except Exception as e:
            logger.warning("Error in ensure_ascii for value '{}': {}".format(value, e), __file__)
            try:
                return ''.join(c for c in str(value) if ord(c) < 128)
            except Exception:
                return ''

    def _strip_namespace(self,tag):
        if '}' in tag:
            return tag.split('}', 1)[1]
        return tag

    def _normalize_vsdata_tag(self,tag_name):
        return re.sub(r'^vsData(?:Data)*', 'vs', tag_name)

    def _get_user_label_from_element(self, elem):
        """
        Extract userLabel from element's attributes section.
        Returns userLabel value if exists and not empty, otherwise returns None.
        """
        try:
            for child in elem:
                if self._strip_namespace(child.tag) == 'attributes':
                    for attr_child in child:
                        if self._strip_namespace(attr_child.tag) == 'userLabel':
                            user_label = attr_child.text
                            if user_label and user_label.strip():
                                return self._ensure_ascii(user_label.strip())
                    break
            return None
        except Exception as e:
            logger.warning("Error extracting userLabel from element: {}".format(e), __file__)
            return None

    def _get_user_label_from_vsdata(self, elem, vs_data_type):
        """
        Extract userLabel from vsData* section within VsDataContainer.
        Returns userLabel value if exists and not empty, otherwise returns None.
        """
        try:
            for child in elem:
                if self._strip_namespace(child.tag) == 'attributes':
                    for attr_child in child:
                        if self._strip_namespace(attr_child.tag) == vs_data_type:
                            for vs_child in attr_child:
                                if self._strip_namespace(vs_child.tag) == 'userLabel':
                                    user_label = vs_child.text
                                    if user_label and user_label.strip():
                                        return self._ensure_ascii(user_label.strip())
                            break
                    break
            return None
        except Exception as e:
            logger.warning("Error extracting userLabel from vsData section: {}".format(e), __file__)
            return None

    def _build_fdn_part(self, fdn_tag, elem_id, elem, vs_data_type=None):
        """
        Build FDN part using userLabel if available and not empty, otherwise use elem_id.
        For VsDataContainer, check userLabel in the vsData* section.
        """
        try:
            user_label = None

            if vs_data_type:
                user_label = self._get_user_label_from_vsdata(elem, vs_data_type)
            else:
                user_label = self._get_user_label_from_element(elem)

            fdn_value = user_label if user_label else elem_id
            return "{}={}".format(fdn_tag, fdn_value)

        except Exception as e:
            logger.warning("Error building FDN part for tag '{}', id '{}': {}".format(fdn_tag, elem_id, e), __file__)
            return "{}={}".format(fdn_tag, elem_id)

    def _process_attributes_for_doc(self, elem, sharedDoc):
        """
        Process attributes for a given element and update the sharedDoc.
        This handles both direct attributes and nested attributes.
        """
        attributes_elem = None
        for child in elem:
            if self._strip_namespace(child.tag) == 'attributes':
                attributes_elem = child
                break

        if attributes_elem is not None:
            for attr in attributes_elem:
                attr_tag = self._strip_namespace(attr.tag)
                attr_text = attr.text or ''
                sharedDoc[attr_tag.upper()] = self._ensure_ascii(attr_text.replace(';', '/').strip())

    def _process_nested_attributes(self, parent_elem):
        attributes = {}

        for child in parent_elem:
            child_tag = self._strip_namespace(child.tag)

            if len(list(child)) == 0:
                child_text = child.text or ''
                child_text = self._ensure_ascii(child_text)
                attributes[child_tag.upper()] = child_text
            else:
                nested_attributes = self._process_nested_attributes(child)
                attributes.update(nested_attributes)

        return attributes

    def _create_and_store_doc(self, fdn, tag, elem_id, baseSharedDoc, active_docs, active_doc_ids, elem, mo_types_by_fdn=None):
        sharedDoc = copy.deepcopy(baseSharedDoc)
        sharedDoc['FDN'] = fdn
        sharedDoc['DATATYPE'] = tag
        sharedDoc['ID'] = str(elem_id) if elem_id else "unknown_id_{}".format(len(active_docs))

        if mo_types_by_fdn is not None:
            mo_types_by_fdn[fdn] = tag

        active_docs[fdn] = sharedDoc
        active_doc_ids[id(elem)] = fdn
        return sharedDoc

    def _update_fdn_for_vsdata_container(self, fdn_stack, vs_data_type_text, parent_vscontainer_id_value, parent_elem):
        if parent_vscontainer_id_value:
            parent_vscontainer_id_value = self._ensure_ascii(parent_vscontainer_id_value)
            placeholder_fdn_part = "VsDataContainer={}".format(parent_vscontainer_id_value)

            user_label = self._get_user_label_from_vsdata(parent_elem, vs_data_type_text)
            fdn_value = user_label if user_label else parent_vscontainer_id_value

            for i in range(len(fdn_stack) - 1, -1, -1):
                if fdn_stack[i] == placeholder_fdn_part:
                    vs_data_type = self._normalize_vsdata_tag(vs_data_type_text)
                    fdn_stack[i] = "{}={}".format(vs_data_type, fdn_value)

    def _process_element_attributes(self, elem, sharedDoc, vs_data_tag, mo_data_tag, element_stack):
        parent_elem = element_stack[-2] if len(element_stack) > 1 else None
        parent_tag = self._strip_namespace(parent_elem.tag) if parent_elem is not None else None
        is_direct_attribute_child = parent_tag == 'attributes'
        is_in_vsdata_block = parent_tag == vs_data_tag
        is_in_modata_block = parent_tag == mo_data_tag
        is_leaf = not list(elem)

        if (is_direct_attribute_child or is_in_vsdata_block or is_in_modata_block) and is_leaf:
            elem_text = elem.text or ''
            attr_value = elem_text.replace(';', '/').strip()
            sharedDoc[self._strip_namespace(elem.tag).upper()] = self._ensure_ascii(attr_value)
        elif (is_direct_attribute_child or is_in_vsdata_block or is_in_modata_block) and not is_leaf:
            nested_attrs = self._process_nested_attributes(elem)
            sharedDoc.update(nested_attrs)

    def _format_datetime_payload(self, raw_datetime):
        if not raw_datetime:
                return ''

        try:
            if raw_datetime.endswith('Z'):
                raw_datetime = raw_datetime[:-1]
            elif len(raw_datetime) > 6 and raw_datetime[-6] in ['-', '+'] and raw_datetime[-3] == ':':
                raw_datetime = raw_datetime[:-6]

            dt_obj = datetime.strptime(raw_datetime, "%Y-%m-%dT%H:%M:%S")
        except ValueError:
            try:
                dt_obj = datetime.strptime(raw_datetime, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                logger.error("Could not parse dateTime string: {}".format(raw_datetime), __file__)
                return ''

        return dt_obj.strftime("%Y-%m-%d %H:%M:%S")

    def _finalize_document(self, doc_fdn, active_docs, active_doc_ids, fdn_stack, mo_types_by_fdn, finalized_docs, elem):
        if doc_fdn and doc_fdn in active_docs:
            sharedDoc = active_docs[doc_fdn]

            current_fdn_str = ','.join(fdn_stack)
            doc_fdn_str = sharedDoc.get('FDN')

            can_finalize = False
            if doc_fdn_str == current_fdn_str:
                can_finalize = True
            else:
                doc_fdn_parts = doc_fdn_str.split(',')
                current_fdn_parts = current_fdn_str.split(',')
                if len(current_fdn_parts) == len(doc_fdn_parts) + 1:
                    base_match = True
                    for i in range(len(doc_fdn_parts)):
                        if doc_fdn_parts[i] != current_fdn_parts[i]:
                            base_match = False
                            break
                    if base_match:
                        last_doc_part_id = doc_fdn_parts[-1].split('=')[-1]
                        last_current_part_id = current_fdn_parts[-1].split('=')[-1]
                        if last_doc_part_id == last_current_part_id:
                            can_finalize = True

            if can_finalize and 'DATATYPE' in sharedDoc:
                processed_doc = copy.deepcopy(sharedDoc)

                if doc_fdn in mo_types_by_fdn:
                    processed_doc['DATATYPE'] = mo_types_by_fdn[doc_fdn]

                processed_doc["DATETIME"] = self._format_datetime_payload(processed_doc.get('DATETIME', ''))
                finalized_docs.append(processed_doc)

            del active_docs[doc_fdn]
            if id(elem) in active_doc_ids:
                del active_doc_ids[id(elem)]

    def process(self, familyObj=FamilyObject(), baseObject={}):
        filesToBeProcessed = familyObj.getFiles()
        familyObj.clearFiles()

        for filePath in filesToBeProcessed:
            fileName = os.path.basename(filePath)
            familyObj.fileName = fileName

            logger.info("[Reader] Reading ZTE CM XML file '{}'...".format(fileName), __file__)
            prefix_filename = ['lte','nr','plat']
            if os.path.getsize(filePath) == 0:
                logger.warning("File {} is empty.".format(fileName), __file__)
                continue
            elif not any(prefix_file in fileName.lower() for prefix_file in prefix_filename):
                logger.warning("Could not determine technology (LTE/NR/PLAT) from filename '{}'.".format(fileName), __file__)

            try:
                baseSharedDoc = self.header_iter(filePath)
                self.fast_iter(filePath, familyObj, baseObject, baseSharedDoc)
            except Exception as e:
                logger.error("Error processing file {}: {}".format(fileName, e), __file__)
                import traceback
                logger.error(traceback.format_exc(), __file__)

    def header_iter(self, filePath):
        sharedDoc = {}
        fileName = os.path.basename(filePath)

        sharedDoc['GRANULARITYPERIOD'] = 1440
        try:
            context = etree.iterparse(filePath, events=('start', 'end'))
            _, root = next(context)
            for event, elem in context:
                tag = self._strip_namespace(elem.tag)
                if event == 'start':
                    if tag == 'fileHeader':
                        sharedDoc['FILEFORMATVERSION'] = self._ensure_ascii(elem.get('fileFormatVersion', ''))
                        sharedDoc['VENDORNAME'] = self._ensure_ascii(elem.get('vendorName', ''))
                    elif tag == 'fileFooter':
                        sharedDoc['DATETIME'] = self._ensure_ascii(elem.get('dateTime', ''))

                if event == 'end':
                    elem.clear()
            root.clear()
            del context
        except etree.ParseError as e:
            logger.error("XML Parse Error in header_iter for {}: {}".format(fileName, e), __file__)
        except Exception as e:
            logger.error("Unexpected Error in header_iter for {}: {}".format(fileName, e), __file__)
        return sharedDoc

    def fast_iter(self, filePath, familyObj, baseObject, baseSharedDoc):
        """
        Fast iteration through XML file
        """
        fileName = os.path.basename(filePath)
        try:
            context = etree.iterparse(filePath, events=('start', 'end'))
            _, root = next(context)
            fdn_stack = []
            element_stack = []

            active_docs = {}
            active_doc_ids = {}
            current_vs_doc = None

            processing_attributes_mo = False
            processing_attributes_vs = False
            vs_data_tag = None
            mo_data_tag = None
            vsc_parent_for_attributes = {}
            mo_parent_for_attributes = {}
            mo_types_by_fdn = {}

            finalized_docs = []
            lte_nr_tags = ['eutranNrm', 'utranNrm', 'nrNrm']

            for event, elem in context:
                tag = self._strip_namespace(elem.tag)
                elem_id = elem.get('id')

                if event == 'start':
                    element_stack.append(elem)
                    try:
                        if elem_id is not None:
                            elem_id = self._ensure_ascii(elem_id)
                            fdn_tag_name = self._strip_namespace(tag)
                            fdn_tag = self._normalize_vsdata_tag(fdn_tag_name)

                            if tag == 'VsDataContainer':
                                fdn_part = "VsDataContainer={}".format(elem_id)
                            else:
                                fdn_part = self._build_fdn_part(fdn_tag, elem_id, elem)

                            fdn_stack.append(fdn_part)

                            if any(tag in elem.tag for tag in lte_nr_tags):
                                current_fdn = ','.join(fdn_stack)
                                sharedDoc = self._create_and_store_doc(current_fdn, tag, elem_id, baseSharedDoc, active_docs, active_doc_ids, elem, mo_types_by_fdn)
                                self._process_attributes_for_doc(elem, sharedDoc)
                                self.standard_mos.append(self._strip_namespace(elem.tag))

                        elif tag == 'attributes':
                            if len(element_stack) > 1:
                                parent_elem_for_attr = element_stack[-2]
                                tag_wihout_namespace = self._strip_namespace(parent_elem_for_attr.tag)
                                if not tag_wihout_namespace in ('SubNetwork','MeContext','ManagedElement'):
                                    if 'VsDataContainer' in tag_wihout_namespace:
                                        vs_data_tag = None
                                        vsc_parent_for_attributes[id(elem)] = parent_elem_for_attr
                                        processing_attributes_vs = True
                                    elif tag_wihout_namespace in self.standard_mos:
                                        mo_data_tag = None
                                        mo_parent_for_attributes[id(elem)] = parent_elem_for_attr
                                        processing_attributes_mo = True

                        elif processing_attributes_vs and tag == 'vsDataType':
                            if elem.text:
                                vs_data_type_text = self._ensure_ascii(elem.text)

                                if len(element_stack) >= 2:
                                    attributes_element = element_stack[-2]
                                    parent_vsc_elem = vsc_parent_for_attributes.get(id(attributes_element))

                                    if parent_vsc_elem is not None:
                                        parent_vscontainer_id_value = parent_vsc_elem.get('id')
                                        self._update_fdn_for_vsdata_container(fdn_stack, vs_data_type_text, parent_vscontainer_id_value, parent_vsc_elem)

                                current_fdn = ','.join(fdn_stack)
                                sharedDoc = self._create_and_store_doc(current_fdn, vs_data_type_text, parent_vscontainer_id_value, baseSharedDoc, active_docs, active_doc_ids, elem)
                                if parent_vsc_elem is not None:
                                    active_doc_ids[id(parent_vsc_elem)] = current_fdn
                                current_vs_doc = sharedDoc

                        elif processing_attributes_vs and tag.startswith('vsData'):
                            vs_data_tag = tag

                        elif processing_attributes_vs:
                            if current_vs_doc:
                                self._process_element_attributes(elem, current_vs_doc, vs_data_tag, mo_data_tag, element_stack)

                        if processing_attributes_mo:
                            parent_fdn = None
                            for ancestor in reversed(element_stack[:-1]):
                                if id(ancestor) in active_doc_ids:
                                    parent_fdn = active_doc_ids[id(ancestor)]
                                    break

                            if parent_fdn and parent_fdn in active_docs:
                                sharedDoc = active_docs[parent_fdn]
                                self._process_element_attributes(elem, sharedDoc, vs_data_tag, mo_data_tag, element_stack)

                    except Exception as e:
                        logger.error("Unexpected Error: {}".format(e), __file__)

                elif event == 'end':

                    is_standard_mo_end = tag in self.standard_mos
                    is_vs_data_container_end = tag == 'VsDataContainer'

                    if (is_standard_mo_end or is_vs_data_container_end) and elem_id is not None:
                        doc_fdn_to_finalize = None
                        if is_vs_data_container_end and id(elem) in active_doc_ids:
                            doc_fdn_to_finalize = active_doc_ids[id(elem)]
                        elif is_standard_mo_end and id(elem) in active_doc_ids:
                            doc_fdn_to_finalize = active_doc_ids[id(elem)]

                        if doc_fdn_to_finalize:
                            self._finalize_document(doc_fdn_to_finalize, active_docs, active_doc_ids, fdn_stack, mo_types_by_fdn, finalized_docs, elem)

                    if tag == 'attributes':
                        if id(elem) in vsc_parent_for_attributes:
                            del vsc_parent_for_attributes[id(elem)]
                            processing_attributes_vs = False
                            vs_data_tag = None
                        if id(elem) in mo_parent_for_attributes:
                            del mo_parent_for_attributes[id(elem)]
                            processing_attributes_mo = False
                            mo_data_tag = None

                    if elem_id is not None:
                        if fdn_stack:
                            fdn_stack.pop()

                    if element_stack and element_stack[-1] == elem:
                        element_stack.pop()

                    elem.clear()

            root.clear()
            del context

            docs_by_type = defaultdict(list)
            for doc in finalized_docs:
                doc_type = doc.get('DATATYPE', 'Unknown')
                docs_by_type[doc_type].append(doc)

            for doc_type, docs in docs_by_type.items():
                unit_id = self._normalize_vsdata_tag(doc_type)
                if hasattr(familyObj, 'setUnitID'):
                    familyObj.setUnitID(unit_id)
                    for doc in docs:
                        data_time_envelope = familyObj.parseEnvelopeDataTime(doc["DATETIME"])
                        granularity_sec = int(doc['GRANULARITYPERIOD'])
                        data_document = {
                            "dataTime": data_time_envelope,
                            "granularitySec": granularity_sec,
                            "data": doc
                        }
                        familyObj.addDocument(data_document)

                    self.nextOp(familyObj=familyObj, baseObject=baseObject)
                    familyObj.clearDocuments()
                else:
                    logger.warning("familyObj does not have setUnitID method. Cannot store result.", __file__)
        except etree.ParseError as e:
            logger.error("XML Parse Error in fast_iter for {}: {}".format(fileName, e), __file__)
        except Exception as e:
            logger.error("Unexpected Error in fast_iter for {}: {}".format(fileName, e), __file__)
            import traceback
            logger.error(traceback.format_exc(), __file__)