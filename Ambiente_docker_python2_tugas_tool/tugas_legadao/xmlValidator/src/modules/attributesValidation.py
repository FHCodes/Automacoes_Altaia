# from Validator.lib.Logger import Logger
from lib.Logger import Logger


class attributesValidation():
    def __init__(self, client, oss, logname):
        self.client = client
        self.oss = oss
        self.logger = Logger(logname).get()

    def validate(self):
        data = {}
        data['table'] = {}
        data['column'] = {}
        data['unit'] = {}
        data['item'] = {}
        warning = False

        self.logger.debug("********** CHECK CONSISTENT IN THE NUMBER OF ATTRIBUTES **********")
        for table in self.client['root']['table']:
            for attr in table.keys():
                try:
                    data['table'][attr] += 1
                except:
                    data['table'][attr] = 1

            if 'column' in table:
                for column in table['column']:
                    for attr in column.keys():
                        try:
                            data['column'][attr] += 1
                        except:
                            data['column'][attr] = 1

        if len(list(set(data['table'].values()))) > 1:
            self.logger.warning("The number of attributes in <table> is not consistent. " + str(data['table']))
            warning = True

        if len(list(set(data['column'].values()))) > 1:
            self.logger.warning("The number of attributes in <column> is not consistent. " + str(data['column']))
            warning = True

        for unit in self.oss['root']['unit']:
            for attr in unit.keys():
                try:
                    data['unit'][attr] += 1
                except:
                    data['unit'][attr] = 1
            if 'item' in unit:
                for item in unit['item']:
                    for attr in item.keys():
                        try:
                            data['item'][attr] += 1
                        except:
                            data['item'][attr] = 1

        if len(list(set(data['unit'].values()))) > 1:
            self.logger.warning("The number of attributes in <unit> is not consistent. " + str(data['unit']))
            warning = True

        if len(list(set(data['item'].values()))) > 1:
            self.logger.warning("The number of attributes in <item> is not consistent. " + str(data['item']))
            warning = True

        if not warning:
            # self.logger.info("The number of attributes is consistent")
            self.logger.success("The number of attributes is consistent")