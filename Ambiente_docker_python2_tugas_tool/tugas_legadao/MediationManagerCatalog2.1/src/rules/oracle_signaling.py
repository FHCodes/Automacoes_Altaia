__doc__ = \
    __version__ = '1.0'
__authors__ = ['Version 1.0: Paulo Gil <paulo-a-gil@alticelabs.com>']

import re
from lib.objects.column import column
from lib.functions import *
import xml.etree.ElementTree as ET

#semelhante a genericHierarchy, trata casos neste formato: site_name#mate_site_name#replchannel_group_id#namespace
#e devolve as regex individualmente para cada campo, ideal para casos onde nao se sabe a ordem pelo qual chegam

def process(unit_dict, config):
    for oss_id in unit_dict.keys():
        measured_object = re.sub(config['regex'], '', unit_dict.get(oss_id).measuredObject)
        measured_object_list = re.split(r'\r|\n|;|#', measured_object)

        objects_list = list()
        
        if config['startField']:
            if isinstance(config['startField'], list):
                objects_list += config['startField']
            else:
                objects_list.append(str(config['startField']))
        
        if config['additionalFields']:
            if isinstance(config['additionalFields'], list):
                measured_object_list += config['additionalFields']
            else:
                measured_object_list.append(str(config['additionalFields']))

        objects_list_tags = dict()

        for base_measured_object in measured_object_list:
            measured_object = re.sub(r',\s|/\s', ',', base_measured_object)
            measured_object_items = (re.sub(r'[/|,| ]', '', measured_object)).strip().split('?')
            measured_object_items_tags = re.sub(r'[/|,|]', '', measured_object).strip().split('?')

            measured_object_items = [item for item in measured_object_items if item != '']
            measured_object_items_tags = [item for item in measured_object_items_tags if item != '']

            try:
                if measured_object_items[-1] == ':':
                    measured_object_items[-1] = re.sub(r'[:]', '2:', measured_object_items[-2])
                if measured_object_items_tags[-1] == ':':
                    measured_object_items_tags[-1] = re.sub(r'[:]', '2:', measured_object_items_tags[-2])
                # measured_object_items_tags[-1] = "{0}2".format(measured_object_items_tags[-2])
            except IndexError:
                pass

            for object in measured_object_items:
                object_id_list = (re.sub('\.|=|-|_|\(|\)|\+', '', object)).split(':')

                if object_id_list[-1] == '':
                    del object_id_list[-1]

                object_id = object_id_list[-1]

                for key in object_id_list[:-2]:
                    if key != object_id_list[-2]:
                        object_id = ('{0}{1}').format(key, object_id)

                objects_list.append(object_id)

            for measured_object_tag in measured_object_items_tags:
                #object_id_list = (re.sub('\.|=|_|-|\(|\)|\+', '', measured_object_tag)).split(':')
                object_id_list = measured_object_tag.split(':')

                if object_id_list[-1] == '':
                    del object_id_list[-1]

                object_id = object_id_list[-1]

                objects_list_tags[(re.sub(" |_", "", object_id)).upper()] = object_id

        for object in objects_list:
            newField = column()
            newField.create(object.upper(), object, validateUdn(object), validateSqlName(object), object, 'ID',
                            'VARCHAR2(256)', 'STRING', 'STRING', '', '')

            if object == str(config['startField']):
                pattern = '^(?P<' + object.upper() + '>[^,/]+)'
            else:
                pattern = '^.*' + '{0}{1}'.format(objects_list_tags[(re.sub(" |_", "", object)).upper()], config[
                    'sepCharPattern']) + '(?P<' + object.upper() + '>[^' + config['interChar'] + ']+)'
            # pattern = '^.*' + '{0}{1}'.format(objects_list_tags[object.replace(" ", "").upper()], config['sepCharPattern']) + '(?P<' + object.upper() + '>[^' + config['interChar'] + ']+)'

            unit_dict.get(oss_id).addAttribute(object.upper(), newField)

            operation = ET.Element("operation")
            operation.set("type", "applyRegex")
            regex = ET.SubElement(operation, "regex")
            regex.set("pattern", pattern)
            new_field = ET.SubElement(regex, "newField")
            new_field.text = object.upper()

            unit_dict.get(oss_id).addOperation('item', str(config['fieldName']), operation)
