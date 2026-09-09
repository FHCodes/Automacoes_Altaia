
# Native libraries
import importlib

# Local libraries
logger = importlib.import_module("shelf.collectorprocess.logger").logger

class ConnectionFactory:

    def __init__(self):
        self._factory = None
        self._connection = None

    # #
    # Gets Connection to factory
    # #
    def getConnection(self):
        pass

    # #
    # Returns connection factory
    # #
    def getFactory(self):
        return self._factory

    # #
    # Executes Query
    # #
    def executeQuery(self, query):
        pass
