__doc__ = \
    __version__ = '1.0'
__authors__ = ['Version 0.1: Joao Pio <joao-t-pio@alticelabs.com>']

import re
import sys
from lib.objects.column import column
from lib.objects.hierarchy import hierarchy
from lib.functions import *


def process(unitDict, config):
    for ossId in unitDict.keys():
        unitObj = unitDict[ossId]

        measuredObjectList = list()

        if ";" in unitObj.measuredObject:
            tmpList = unitObj.measuredObject.split(";")
            for measObj in tmpList:
                if "," in measObj:
                    measuredObjectList.extend(measObj.split(","))
                else:
                    measuredObjectList.append(measObj)
        elif "," in unitObj.measuredObject:
            tmpList = unitObj.measuredObject.split(",")
            for measObj in tmpList:
                if ";" in measObj:
                    measuredObjectList.extend(measObj.split(";"))
                else:
                    measuredObjectList.append(measObj)
        else:
            measuredObjectList.append(unitObj.measuredObject)

        measuredObjectList = list(set(measuredObjectList))

        # Create a temp measuredObject without spaces for the hierarchy building process
        measuredObject = re.sub(r' ', '', unitObj.measuredObject)

        # Update the measuredObject in the unit with the unique values
        unitObj.measuredObject = ", ".join(measuredObjectList)

        if config['regex'] != '':
            measuredObject = re.sub(config['regex'], '', unitObj.measuredObject)

        createHierarchy(unitObj, config, measuredObject)


def createHierarchy(unitObj, config, measuredObject):
    measuredObjectList = list()

    if ";" in measuredObject:
        tmpList = measuredObject.split(";")
        for measObj in tmpList:
            if "," in measObj:
                measuredObjectList.extend(measObj.split(","))
            else:
                measuredObjectList.append(measObj)
    elif "," in measuredObject:
        tmpList = measuredObject.split(",")
        for measObj in tmpList:
            if ";" in measObj:
                measuredObjectList.extend(measObj.split(";"))
            else:
                measuredObjectList.append(measObj)
    else:
        measuredObjectList.append(measuredObject)

    measuredObjectList = list(set(measuredObjectList))

    for measObj in measuredObjectList:
        newHierarchy = hierarchy()
        newHierarchy.create("#".join(measuredObjectList), list())
        pattern = '^'

        measObj = re.sub(r'\/type=.+?\/(.*:[^\[])?', "", measObj)

        attributes = re.findall(r'\[(.*?)\]', measObj)
        pattern += measObj

        for attribute in attributes:
            newField = column()
            newField.create(attribute.upper(), attribute, attribute, validateSqlName(attribute.upper()), attribute,
                            'ID', 'VARCHAR2(256)', 'STRING', 'STRING', 'STRING', '')

            regexField = '(?P<' + attribute.upper() + '>[^' + config['interChar'] + ']+?)'
            pattern = pattern.replace("[{0}]".format(attribute), regexField)

            newHierarchy.addNewField(attribute)
            unitObj.addAttribute(attribute, newField)

        pattern = pattern.replace(".", "\.")
        newHierarchy.pattern = pattern + '$'
        unitObj.addHierarchy(pattern, newHierarchy)
