# from Validator.lib.Logger import Logger
from lib.Logger import Logger


class partitionOfValidation():
    def __init__(self, client, logname):
        self.client = client
        self.logger = Logger(logname).get()

    def validate(self):
        error = False

        self.logger.debug("********** PARTITION OF VALIDATION **********")
        for table in self.client['root']['table']:
            if "column" in table:
                tam = len(table['column'])
                if tam > 999:
                    self.logger.error("[" + table['tableName'] + "] has more than 999 columns")
                    error = True
                elif tam > 980:
                    self.logger.warning("[" + table['tableName'] + "] it\'s almost at the items limit")
                    error = True

        if not error:
            # self.logger.info("The field 'partition of' is valid")
            self.logger.success("The field 'partition of' is valid")
