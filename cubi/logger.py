import logging

class Logger:
    _debug = False

def enable_debug_log():
    Logger._debug = True

def is_debug():
    return Logger._debug

def get_logger():
    return logging.getLogger()
