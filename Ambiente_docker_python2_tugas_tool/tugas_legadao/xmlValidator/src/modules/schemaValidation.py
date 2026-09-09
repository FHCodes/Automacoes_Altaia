from lxml import etree
# from Validator.lib.Logger import Logger
from lib.Logger import Logger


class schemaValidation():
    def __init__(self, logname):
        self.logger = Logger(logname).get()

    def schemaValidatorClient(self, catalog):
        self.logger.debug("********** XSD VALIDATION TO CLIENT CATALOG **********")
        try:
            schema = etree.XMLSchema(file='conf/schema_CLIENT_Catalog.xsd')
            schema.assertValid(catalog)
            # self.logger.info("Client Catalog is valid!")
            self.logger.success("Client Catalog is valid!")
        except etree.DocumentInvalid, xml_errors:
            for error in xml_errors.error_log:
                self.logger.error("[LINE: [{0}] {1}".format(error.line, error.message))

    def schemaValidatorOss(self, catalog):
        self.logger.debug("********** XSD VALIDATION TO OSS CATALOG **********")
        try:
            schema = etree.XMLSchema(file='conf/schema_OSS_Catalog.xsd')
            schema.assertValid(catalog)
            # self.logger.info("OSS Catalog is valid!")
            self.logger.success("OSS Catalog is valid!")
        except etree.DocumentInvalid, xml_errors:
            for error in xml_errors.error_log:
                self.logger.error("[LINE: [{0}] {1}".format(error.line, error.message))

    def schemaValidatorOperations(self, catalog):
        self.logger.debug("********** XSD VALIDATION TO OPERATIONS CATALOG **********")
        try:
            schema = etree.XMLSchema(file='conf/schema_OPERATIONS_Catalog.xsd')
            schema.assertValid(catalog)
            # self.logger.info("Operations Catalog is valid!")
            self.logger.success("Operations Catalog is valid!")
        except etree.DocumentInvalid, xml_errors:
            for error in xml_errors.error_log:
                self.logger.error("[LINE: [{0}] {1}".format(error.line, error.message))
