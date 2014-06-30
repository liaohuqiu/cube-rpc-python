import json
import logging

try:  # Python 2.7+
    from logging import NullHandler
except ImportError:
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass

class Logger:

    _logger = None
    _debug = False

    @staticmethod
    def get_instance():
        if Logger._logger == None:
            Logger._logger = get_null_logger()
        return Logger._logger

def enable_debug_log():
    Logger._debug = True
    Logger._logger = get_console_logger(logging.DEBUG)

def is_debug():
    return Logger._debug

def get_logger():
    return Logger.get_instance()

def set_logger(logger):
    Logger._logger = logger
    pass

def _attach_handler(logger, handlers):
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')

    for h in handlers:
        h.setFormatter(formatter)
        logger.addHandler(h)

def _make_logger(name, level = logging.INFO, handlers = (logging.StreamHandler())):
    logger = logging.getLogger(name)
    logger.setLevel(level)
    _attach_handler(logger, handlers)
    return logger

def get_null_logger():
    return _make_logger('null', logging.INFO, (NullHandler(),))

def get_console_logger(level = logging.INFO):
    return _make_logger('console', level, (logging.StreamHandler(),))
