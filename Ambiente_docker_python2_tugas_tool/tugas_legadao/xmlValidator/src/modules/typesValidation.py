# from Validator.lib.Logger import Logger
from lib.Logger import Logger
from collections import OrderedDict


class typesValidation():
    def __init__(self, client, oss, operations, catalogtype, logname):
        self.client = client
        self.operations = operations
        self.oss = oss
        self.catalogtype = catalogtype
        self.logger = Logger(logname).get()


    def validateDBTypeAndTypeCust(self):
        warning = False

        # PODERA SER NECESSARIO ADICIONAR MAIS...
        datatypes = {
            "NUMBER": [
                "INTEGER",
                "COUNTER",
                "COUNTER8",
                "COUNTER16",
                "COUNTER32",
                "COUNTER64"
            ],
            "VARCHAR2": [
                "STRING"
            ],
            "TIMESTAMP": [
                "TIMESTAMP"
            ]
        }

        self.logger.debug("********** COMPARE BDTYPE AND TYPECUST **********")

        for table in self.client['root']['table']:
            for unit in self.oss['root']['unit']:
                if table['ossId'] == unit['id']:
                    if 'column' in table:
                        for column in table["column"]:
                            for item in unit["item"]:
                                if column["id"] == item["id"]:
                                    try:
                                        bdtype = column['bdtype'].split("(",1)[0]
                                    except:
                                        bdtype = column['bdtype']

                                    if item['typeCust'] not in datatypes[bdtype]:
                                        self.logger.error("[" + table["tableName"] + "][" + column["bdcolname"] + 
                                            "] " + "DATA TYPE IS NOT CONSISTENT - " +  "BDTYPE: " + column["bdtype"] +
                                            " TYPECUST: " + item["typeCust"])
                                        warning = True

        if not warning:
            self.logger.success("bdtype/typeCust are consistent")

    def validateDBN0andBDtype(self):
        warning = False

        self.logger.debug("********** CHECK FOR INCONSISTENT TYPES DBN0/BDTYPE **********")
        if self.catalogtype == 'PM':
            for table in self.client['root']['table']:
                if 'column' in table:
                    for column in table['column']:
                        dbn0 = column['dbn0type']
                        bdtype = column['bdtype']
                        if dbn0 != 'PK' and "VARCHAR" in bdtype:
                            if dbn0 not in ['ID', 'ENRICH']:
                                self.logger.warning("[" + table['tableName'] + "][" + column['bdcolname'] + "] BD type is "
                                                                                                            "VARCHAR and DBN0"
                                                                                                            " Type is not ID")
                                warning = True

                        elif dbn0 != 'PK' and "NUMBER" in bdtype:
                            if dbn0 != 'MT':
                                self.logger.warning("[" + table['tableName'] + "][" + column['bdcolname'] + "] BD type is "
                                                                                                            "NUMBER and DBN0"
                                                                                                            " Type is not MT")
                                warning = True

        if not warning:
            # self.logger.info("bdtype/dbn0type are consistent")
            self.logger.success("bdtype/dbn0type are consistent")

    def validateDBN0(self):
        error = False

        self.logger.debug("********** CHECK FOR INCONSISTENT TYPES CATALOG/DBN0TYPE **********")
        if 'PM' == self.catalogtype:
            notdbn0 = 'CM'
        elif 'CM' == self.catalogtype:
            notdbn0 = 'MT'

        for table in self.client['root']['table']:
            if 'column' in table:
                for column in table['column']:
                    if column['dbn0type'] in notdbn0:
                        self.logger.error("dbn0type <" + column['dbn0type'] + "> in [" + table['tableName'] + "]["
                                        + column['bdcolname'] + "] is not allowed")
                        error = True

        if not error:
            # self.logger.info("catalog/dbn0type are consistent")
            self.logger.success("catalog/dbn0type are consistent")

    def validateEnrich(self):
        error = False
        clientDict = dict()

        self.logger.debug("********** VALIDATE ENRICH TYPE **********")

        for table in self.client["root"]["table"]:
            tableid = table["id"].upper()
            clientDict[tableid] = dict()
            if 'column' in table:
                for column in table["column"]:
                    columnid = column["id"].upper()
                    clientDict[tableid][columnid] = column["dbn0type"]

        if 'unit' in self.operations["root"]:
            if 'PM' != self.catalogtype:
                self.logger.info("CM Catalog does not require this validation")
                return
        
            for unit in self.operations["root"]["unit"]:
                unitid = unit["id"].upper()

                if unitid not in clientDict:
                    continue

                if "operation" in unit:
                    if type(unit["operation"]) == OrderedDict:
                        if unit["operation"]["type"] == 'enrichment':
                            if type(unit["operation"]["newField"]) != unicode:
                                for newF in unit["operation"]["newField"]:
                                    newF = newF.upper()
                                    if newF in clientDict[unitid]:
                                        if clientDict[unitid][newF] != "ENRICH":
                                            self.logger.error("<id> [{0}][{1}] should be 'enrich' in dbn0type".format(unitid,
                                                                                                                      newF))
                                            error = True
                                    else:
                                        self.logger.error("Enrich Field <{0}> does not found in client".format(newF))
                                        error = True
                            else:
                                newF = unit["operation"]["newField"].upper()
                                if newF in clientDict[unitid]:
                                    if clientDict[unitid][newF] != "ENRICH":
                                        self.logger.error("<id> [{0}][{1}] should be 'enrich' in dbn0type".format(unitid,
                                                                                                                  newF))
                                        error = True
                                else:
                                    self.logger.error("Enrich Field <{0}> does not found in client".format(newF))
                                    error = True
                    else:
                        for operation in unit["operation"]:
                            if operation["type"] == 'enrichment':
                                if type(operation["newField"]) != unicode:
                                    for newF in operation["newField"]:
                                        newF = newF.upper()
                                        if newF in clientDict[unitid]:
                                            if clientDict[unitid][newF] != "ENRICH":
                                                self.logger.error(
                                                    "<id> [{0}][{1}] should be 'enrich' in dbn0type".format(unitid,
                                                                                                            newF))
                                                error = True
                                        else:
                                            print unitid, newF
                                else:
                                    newF = operation["newField"].upper()
                                    if newF in clientDict[unitid]:
                                        if clientDict[unitid][newF] != "ENRICH":
                                            self.logger.error("<id> [{0}][{1}] should be 'enrich' in dbn0type".format(unitid,
                                                                                                                      newF))
                                            error = True
                                    else:
                                        print unitid, newF

        if not error:
            # self.logger.info("The enrichment fields are well")
            self.logger.success("The enrichment fields are well")

    def existsCMorMTtype(self):
        error = False

        self.logger.debug("********** CHECK FOR CM/MT TYPE IN MO **********")
        for table in self.client["root"]["table"]:
            flag = True
            if 'column' in table:
                for column in table["column"]:
                    if column["dbn0type"] in ('MT', 'CM') and column['bdcolname'].upper() not in ('INTERVAL', 'GRANULARITY',
                                                                                        'PERIOD', 'GRANULARITYPERIOD'):
                        flag = False
            if flag:
                self.logger.error("[" + table["tableName"] + "] was not found CM/MT dbn0type")
                error = True

        if not error:
            # self.logger.info("There is at least one CM/MT dbn0type in all units")
            self.logger.success("There is at least one CM/MT dbn0type in all units")

    def validatePrimaryKey(self):
        error = False

        self.logger.debug("********** CHECK FOR PRIMARY KEY IN MO **********")
        for table in self.client['root']['table']:
            flag = True
            if 'column' in table:
                for column in table['column']:
                    if column['dbn0type'] == 'PK':
                        flag = False
                        continue
            if flag:
                self.logger.error("[" + table['tableName'] + "] was not found <PK> in table")
                error = True

        if not error:
            # self.logger.info("<PK> fields are correct")
            self.logger.success("<PK> fields are correct")
