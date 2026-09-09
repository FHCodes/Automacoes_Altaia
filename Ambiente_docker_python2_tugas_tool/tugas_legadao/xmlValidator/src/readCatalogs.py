# import xmltodict
from lib import xmltodict
from lxml import etree as ET


class readCatalogs():
    def __init__(self, catalog):
        client = catalog.replace('#', 'client')
        oss = catalog.replace('#', 'oss')
        operations = catalog.replace('#', 'operations')

        self.clientInfo = self.loadCatalogToDict('./catalogs/'+client)
        self.ossInfo = self.loadCatalogToDict('./catalogs/' + oss)
        self.operationsInfo = self.loadCatalogToDict('./catalogs/' + operations)

        self.clientXML = self.loadCatalogXML('./catalogs/'+client)
        self.ossXML = self.loadCatalogXML('./catalogs/' + oss)
        self.operationsXML = self.loadCatalogXML('./catalogs/' + operations)

    def loadCatalogToDict(self, catalog):
        list_fields = ['table', 'column', 'unit', 'item']
        with open(catalog) as fd:
            data = xmltodict.parse(fd.read(), attr_prefix='', xml_attribs=True, force_list=list_fields)

        return data

    def loadCatalogXML(self, catalog):
        tree = ET.parse(catalog)
        root = tree.getroot()

        return root

    @property
    def getClientInfo(self):
        return self.clientInfo

    @property
    def getOssInfo(self):
        return self.ossInfo

    @property
    def getOperationsInfo(self):
        return self.operationsInfo

    @property
    def getClientXML(self):
        return self.clientXML

    @property
    def getOssXML(self):
        return self.ossXML

    @property
    def getOperationsXML(self):
        return self.operationsXML


