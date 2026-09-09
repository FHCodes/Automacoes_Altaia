"""
from Validator.src.modules.schemaValidation import *
from Validator.src.modules.compareCatalogs import *
from Validator.src.modules.partitionOfValidation import *
from Validator.src.modules.reservedWordsValidation import *
from Validator.src.modules.typesValidation import *
from Validator.src.modules.denyCharValidation import *
from Validator.src.modules.attributesValidation import *
from Validator.src.readCatalogs import readCatalogs
from Validator.lib.Logger import Logger
"""
from src.modules.schemaValidation import *
from src.modules.compareCatalogs import *
from src.modules.partitionOfValidation import *
from src.modules.reservedWordsValidation import *
from src.modules.typesValidation import *
from src.modules.denyCharValidation import *
from src.modules.attributesValidation import *
from src.modules.versionValidation import *
from src.readCatalogs import readCatalogs
from lib.Logger import Logger
import ConfigParser
import sys
import os
import time


def main():
    config = ConfigParser.ConfigParser()
    config.readfp(open(r'conf/validator.cfg'))
    catalog = config.get('DEFAULT', 'catalog')
    catalogtype = config.get('DEFAULT', 'catalogtype')
    denychar = config.get('OTHERS', 'denycharacters')
    logname = config.get('DEFAULT', 'catalog').replace("_#", "").replace(".xml", "_") + time.strftime("%Y%m%d%H%M%S")
    modules = dict(config.items('MODULES'))

    logger = Logger(logname).get()

    print "\n"

    # ADD ASCII ART
    handler = logger.handlers[0]

    flog = open(handler.baseFilename, 'w')
    with open(r'lib/logo', 'r') as f:
        for line in f:
            text = line.rstrip()
            print text
            flog.write(text + '\n')
    flog.write('\n')
    flog.close()

    logger.debug("####### START TIME: {0} ########".format(time.strftime("%Y.%m.%d %H:%M:%S")))

    if catalogtype == 'PM':
        if 'parameters' in catalog:
            logger.warning("[CONFIGURATION] Catalog type does not match with configuration. Expected: 'CM'")
    elif catalogtype == 'CM':
        if 'performance' in catalog:
            logger.warning("[CONFIGURATION] Catalog type does not match with configuration. Expected: 'PM'")

    # DICT
    reader = readCatalogs(catalog)
    clientInfo = reader.getClientInfo
    ossInfo = reader.getOssInfo
    operationsInfo = reader.getOperationsInfo
    # XML
    clientXML = reader.getClientXML
    ossXML = reader.getOssXML
    operationsXML = reader.getOperationsXML

    # SCHEMA VALIDATOR
    schemavalidator = schemaValidation(logname)
    classname = schemavalidator.__class__.__module__.rsplit('.', 1)[1].lower()
    if modules.get(classname).lower() == 'true':
        schemavalidator.schemaValidatorClient(clientXML)
        schemavalidator.schemaValidatorOss(ossXML)
        schemavalidator.schemaValidatorOperations(operationsXML)

    # COMPARE CLIENT - OSS AND CLIENT - OPERATIONS
    compCatalogs = compareCatalogs(clientInfo, ossInfo, operationsInfo, logname)
    classname = compCatalogs.__class__.__module__.rsplit('.', 1)[1].lower()
    if modules.get(classname).lower() == 'true':
        compCatalogs.compareClOss()
        compCatalogs.compareClOp()

    # VALIDATE PARTITION OF
    partof = partitionOfValidation(clientInfo, logname)
    classname = partof.__class__.__module__.rsplit('.', 1)[1].lower()
    if modules.get(classname).lower() == 'true':
        partof.validate()

    # CHECK RESERVED WORDS USAGE
    reserved = reservedWordsValidation(clientInfo, logname)
    classname = reserved.__class__.__module__.rsplit('.', 1)[1].lower()
    if modules.get(classname).lower() == 'true':
        reserved.validate()

    # COMPARE DBN0TYPE - BDTYPE and CATALOG - DBN0TYPE
    types = typesValidation(clientInfo, ossInfo, operationsInfo, catalogtype, logname)
    classname = types.__class__.__module__.rsplit('.', 1)[1].lower()
    if modules.get(classname).lower() == 'true':
        types.validateDBN0andBDtype()
        types.validateDBTypeAndTypeCust()
        types.validateDBN0()
        types.validateEnrich()
        types.existsCMorMTtype()
        types.validatePrimaryKey()

    # CHECK FOR DENY CHARACTERS
    deny = denyCharValidation(clientInfo, ossInfo, denychar, logname)
    classname = deny.__class__.__module__.rsplit('.', 1)[1].lower()
    if modules.get(classname).lower() == 'true':
        deny.validate()

    # CHECK NUMBER OF ATTRIBUTES IS CONSISTENT
    attrvalidation = attributesValidation(clientInfo, ossInfo, logname)
    classname = attrvalidation.__class__.__module__.rsplit('.', 1)[1].lower()
    if modules.get(classname).lower() == 'true':
        attrvalidation.validate()

    # CHECK OSSVERSION (ROOT) AND V (ITEM OSS)
    validateversion = validateVersion(clientInfo, ossInfo, operationsInfo, logname)
    classname = attrvalidation.__class__.__module__.rsplit('.', 1)[1].lower()
    if modules.get(classname).lower() == 'true':
        validateversion.validateOssVersion()
        validateversion.validateVersion()

    logger.debug("####### END TIME: {0} ########".format(time.strftime("%Y.%m.%d %H:%M:%S")))

    print "\nOutput saved in: {0}.log\n".format(logname)


if __name__ == "__main__":
    sys.path.append(os.getcwd())
    main()
