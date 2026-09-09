import logging


class NamfLogger:

    # Class Constructor
    def __init__(self, loglevel=logging.ERROR):
        # Logging formats
        self.FORMAT_CLEAN = "%(levelname)8s: %(message)s"
        self.FORMAT_DETAILED = "[%(filename)10s:%(lineno)4s - %(funcName)15s()] 	%(levelname)8s: %(message)s"

        # Logging definition
        self.log = logging.getLogger('NamfLogger')
        self.log_handler = logging.StreamHandler()  # Handler for the logger
        self.log_handler.setFormatter(logging.Formatter(self.FORMAT_CLEAN))
        self.log.addHandler(self.log_handler)
        self.log.setLevel(loglevel)

    def set_format(self, format="%(levelname)8s: %(message)s"):
        # Set the format
        self.log_handler.setFormatter(logging.Formatter(format))

    def set_level(self, level):
        # Set warning level
        self.log.setLevel(level)


namf_logger = NamfLogger()
