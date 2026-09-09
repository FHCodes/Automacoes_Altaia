__authors__ = [
    "Version 0.1: Bruno Silva <bruno-e-silva@alticelabs.com>"
]

import json, os
import importlib

# Local libraries
logger = importlib.import_module("shelf.collectorprocess.logger").logger


class HierarchyManager():

    # Class Constructor
    def __init__(self, options={}):
        self._primary_keys = json.load(open(
            '/opt/alticelabs/namf/src/shelf/collectorprocess/operators/Readers/HUAWEI/XML/GEXPORT/primary_keys.json'))
        self._identifiers_atributes = json.load(open(
            '/opt/alticelabs/namf/src/shelf/collectorprocess/operators/Readers/HUAWEI/XML/GEXPORT/identifiers_atributes.json'))

    def validateClass(self, className):
        if className in self._primary_keys.keys():
            return True
        return False

    def buildFDN(self, newDocument):
        if newDocument["NECLASSNAME"] == "BSC6900GSM" or newDocument["NECLASSNAME"] == "BSC6900UMTS" or newDocument[
            "NECLASSNAME"] == "BSC6910UMTS" or newDocument["NECLASSNAME"] == "BSC6910GSM" or newDocument["NECLASSNAME"] == "BSC6900GU":
            doc_file_version = "2G3G"
        elif newDocument["NECLASSNAME"] == "BTS3900" or newDocument["NECLASSNAME"] == "BTS5900" or newDocument[
            "NECLASSNAME"] == "LTE" or newDocument["NECLASSNAME"] == "MICROBTS3900"  or newDocument[
            "NECLASSNAME"] == "NODEB":
            doc_file_version = "SRAN"
        else:
            logger.warning("NECLASSNAME {0} not mapped".format(newDocument["NECLASSNAME"]))
            return newDocument

        newDocument["MOINDEX"] = newDocument["ELEMENTNAME"]
        try:
            if doc_file_version in self._primary_keys[newDocument["CLASSNAME"]]:
                if "FDN" not in newDocument:
                    if "NE_NAME" in newDocument:
                        newDocument["FDN"] = newDocument["ELEMENTNAME"] + "," + "NE_NAME=" + newDocument["NE_NAME"]
                        newDocument["NAME"] = newDocument["FDN"]
                    elif "BSC_NAME" in newDocument:
                        newDocument["FDN"] = newDocument["ELEMENTNAME"] + "," + "NE_NAME=" + newDocument["BSC_NAME"]
                        newDocument["NAME"] = newDocument["FDN"]
                    elif "RNC_NAME" in newDocument:
                        newDocument["FDN"] = newDocument["ELEMENTNAME"] + "," + "NE_NAME=" + newDocument["RNC_NAME"]
                        newDocument["NAME"] = newDocument["FDN"]
                    elif "ENODEB_NAME" in newDocument:
                        newDocument["FDN"] = newDocument["ELEMENTNAME"] + "," + "NE_NAME=" + newDocument["ENODEB_NAME"]
                        newDocument["NAME"] = newDocument["FDN"]
                    elif "GNODEBNAME" in newDocument:
                        newDocument["FDN"] = newDocument["ELEMENTNAME"] + "," + "NE_NAME=" + newDocument["GNODEBNAME"]
                        newDocument["NAME"] = newDocument["FDN"]
                    else:
                        newDocument["FDN"] = newDocument["ELEMENTNAME"]

                for key in self._primary_keys[newDocument["CLASSNAME"]][doc_file_version]:
                    try:
                        newDocument["MOINDEX"] = newDocument["MOINDEX"] + "_" + newDocument[key]
                        newDocument["FDN"] += "," + key + "=" + newDocument[key]
                    except KeyError:
                        pass

            else:
                if "BSC_NAME" in newDocument:
                    newDocument["FDN"] = "NE_NAME=" + newDocument["BSC_NAME"]

                elif "RNC_NAME" in newDocument:
                    newDocument["FDN"] = "NE_NAME=" + newDocument["RNC_NAME"]

                elif "ENODEB_NAME" in newDocument:
                    newDocument["FDN"] = "NE_NAME=" + newDocument["ENODEB_NAME"]

                elif "GNODEBNAME" in newDocument:
                    newDocument["FDN"] = "NE_NAME=" + newDocument["GNODEBNAME"]

                elif "ELEMENTNAME" in newDocument:
                    newDocument["FDN"] = "NE_NAME=" + newDocument["ELEMENTNAME"]

                elif "NE_NAME" in newDocument:
                    newDocument["FDN"] = "NE_NAME=" + newDocument["NE_NAME"]
                else:
                    logger.warning("MO [{0}] does not have defined primary keys".format(newDocument["CLASSNAME"]))
        except Exception as e:
            pass

        if doc_file_version in self._identifiers_atributes[newDocument["CLASSNAME"]]:
            sep = ""
            newDocument["FILTERPI"] = ""
            for key in self._identifiers_atributes[newDocument["CLASSNAME"]][doc_file_version]:
                try:
                    newDocument["FILTERPI"] = '{0}{1}{2}={3}'.format(newDocument["FILTERPI"], sep, key,newDocument[key])
                    sep = ','
                except KeyError:
                    pass

        newDocument.pop("NECLASSNAME")
        return newDocument
