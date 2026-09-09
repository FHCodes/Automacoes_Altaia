__doc__ = \
	__version__ = '1.0'
__authors__ = ['Version 0.1: Ricardo Auxiliar <ricardo-d-auxiliar@alticelabs.com>']

import os
import logging


class Logger(object):
    def __init__(self, name):
        name = name.replace('.log', '')
        logger = logging.getLogger('log_namespace.%s' % name)    # log_namespace can be replaced with your namespace
        logger.setLevel(logging.DEBUG)

        # set success level
        logging.SUCCESS = 25  # between WARNING and INFO
        logging.addLevelName(logging.SUCCESS, 'SUCCESS')
        setattr(logger, 'success', lambda message, *args: logger._log(logging.SUCCESS, message, args))

        if not logger.handlers:
            file_name = os.path.join('./logs/', '%s.log' % name)
            handler = logging.FileHandler(file_name)
            formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
            handler.setFormatter(formatter)
            handler.setLevel(logging.DEBUG)
            logger.addHandler(handler)
        self._logger = logger

    def get(self):
        return self._logger
