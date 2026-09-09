import re
from lib.Logger import Logger


class validateVersion():
    def __init__(self, client, oss, operations, logname):
        self.client = client
        self.oss = oss
        self.operations = operations
        self.logger = Logger(logname).get()

    def validateOssVersion(self):
        error = False
        reg = re.compile(r'^([a-zA-Z0-9/._]*)$')

        self.logger.debug("********** CHECK RULES FOR ROOT OSSVERSION**********")

        if not re.search(reg, self.client['root']['ossversion']):
            error = True
        if not re.search(reg, self.oss['root']['ossversion']):
            error = True
        if not re.search(reg, self.operations['root']['ossversion']):
            error = True

        if error:
            self.logger.error("Root <ossversion> does not follow the rules")
        else:
            self.logger.success("Root <ossversion> is valid")

    def validateVersion(self):
        error = False
        reg = re.compile(r'^([a-zA-Z0-9._]+)/([a-zA-Z0-9._]+)$')

        self.logger.debug("********** CHECK RULES FOR ATTRIBUTE V IN OSS ITEM **********")

        for unit in self.oss['root']['unit']:
            if 'item' in unit:
                for item in unit['item']:
                    if 'v' in item:
                        if not re.search(reg, item['v']):
                            error = True
                            self.logger.error("[{0}][{1}] <v> does not follow the rules {2}".format(unit['id'], item['id'],item['v']))
                    # else:
                    #    error = True
                    #    self.logger.error("[{0}][{1}] attribute <v> was not found")

        if not error:
            self.logger.success("Attribute <v> is valid in all items")
