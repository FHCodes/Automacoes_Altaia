# from Validator.lib.Logger import Logger
from lib.Logger import Logger
import json


class reservedWordsValidation():
    def __init__(self, client, logname):
        self.reserved = json.load(open('./conf/reserved.json'))['reserved']
        self.client = client
        self.logger = Logger(logname).get()

    def validate(self):
        error = False

        self.logger.debug("********** CHECK FOR RESERVED WORDS **********")
        for table in self.client['root']['table']:
            if [r for r in self.reserved if table['tableName'].upper() == r]:
                self.logger.error("tableName <" + table['tableName'] + "> is a reserved word in ORACLE or PostgreSQL")
                error = True
            if 'column' in table:
                for column in table['column']:
                    if [r for r in self.reserved if column['bdcolname'].upper() == r]:
                        self.logger.error("[" + table['tableName'] + "]<" + column['bdcolname'] +
                                          "> is a ""reserved ""word in ORACLE or PostgreSQL")
                        error = True

        if not error:
            # self.logger.info("There are no reserved words in catalog")
            self.logger.success("There are no reserved words in catalog")
