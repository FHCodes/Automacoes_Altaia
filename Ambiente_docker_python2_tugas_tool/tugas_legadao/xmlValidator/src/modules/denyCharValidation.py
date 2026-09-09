# from Validator.lib.Logger import Logger
from lib.Logger import Logger


class denyCharValidation():
    def __init__(self, client, oss, deny, logname):
        self.client = client
        self.oss = oss
        self.deny = deny.replace(" ", "").split(',')
        self.logger = Logger(logname).get()

    def validate(self):
        error = False

        self.logger.debug("********** CHECK FORBIDDEN CHARACTERS **********")
        for table in self.client['root']['table']:
            for kt, vt in table.items():
                if any(s in vt for s in self.deny):
                    self.logger.error("TABLE: [{0}] - Field <{1}> has a forbidden character".format(
                        table["tableName"], kt))
                    error = True
            if 'column' in table:
                for column in table['column']:
                    for kc, vc in column.items():
                        denied = [s for s in vc if s in self.deny]
                        if len(denied) > 0:
                            if kc == u'oid' and set(denied) <= {u'<', u'>'}:
                                continue
                            else:
                                self.logger.error("COLUMN: [{0}][{1}] - Field <{2}> has a forbidden character".format(
                                    table["tableName"], column["bdcolname"], kc))
                                error = True

        for unit in self.oss['root']['unit']:
            for ku, vu in unit.items():
                if any(s in vu for s in self.deny):
                    self.logger.error("UNIT: [{0}] - Field <{1}> has a forbidden character".format(
                                      unit["id"], ku))
                    error = True
            
            if 'item' in unit:
                for item in unit['item']:
                    for ki, vi in item.items():
                        if any(s in vi for s in self.deny):
                            self.logger.error("ITEM: [{0}][{1}] - Field <{2}> has a forbidden character".format(
                                unit["id"], item["id"], ki))
                            error = True

        if not error:
            # self.logger.info("No forbidden characters found")
            self.logger.success("No forbidden characters found")
