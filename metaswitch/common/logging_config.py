# @file logging_config.py
#
# Copyright (C) Metaswitch Networks 2016
# If license terms are provided to you in a COPYING file in the root directory
# of the source code repository by which you are accessing this code, then
# the license outlined in that COPYING file applies to your use.
# Otherwise no rights are granted except for those provided to you by
# Metaswitch Networks in a separate written agreement.

import time
import os, sys, traceback
from datetime import datetime
import logging
from logging.handlers import BaseRotatingHandler, SysLogHandler

# Make the same log formatters available to test code, event though
# it doesn't want to use the full logging config.
THREAD_FORMAT = logging.Formatter('%(asctime)s.%(msecs)03d UTC %(levelname)s %(filename)s:%(lineno)d (thread %(threadName)s): %(message)s', "%d-%m-%Y %H:%M:%S")
NO_THREAD_FORMAT = logging.Formatter('%(asctime)s.%(msecs)03d UTC %(levelname)s %(filename)s:%(lineno)d: %(message)s', "%d-%m-%Y %H:%M:%S")
NO_TIME_FORMAT = logging.Formatter('%(levelname)s %(filename)s:%(lineno)d: %(message)s')


def getCurrentFilename(currentTime, log_dir, prefix):
    filename = "{prefix}_{year}{month:02}{day:02}T{hour:02}0000Z.txt".format(prefix=prefix,
                                                                             year=currentTime.year,
                                                                             month=currentTime.month,
                                                                             day=currentTime.day,
                                                                             hour=currentTime.hour)
    return os.path.join(log_dir, filename)

class ClearwaterLogHandler(BaseRotatingHandler):
    def __init__(self, log_directory, logfile_prefix):
        BaseRotatingHandler.__init__(self, "", 'a', encoding=None, delay=True)
        self._log_directory = log_directory
        self._logfile_prefix = logfile_prefix
        self.doRollover()

    def shouldRollover(self, record): #pragma: no cover
        now = int(time.time())
        return (now > self.next_file_change)

    def doRollover(self):
        tmpstream = self.stream
        self.stream = None
        if tmpstream:
            tmpstream.close() #pragma: no cover
        currentTime = int(time.time())
        self.baseFilename = getCurrentFilename(datetime.utcfromtimestamp(currentTime),
                                               self._log_directory,
                                               self._logfile_prefix)
        self.stream = os.fdopen(os.open(self.baseFilename, os.O_WRONLY | os.O_CREAT, 0644), self.mode)
        self.next_file_change = (int(currentTime / 3600) * 3600) + 3600

def configure_logging(log_level,
                      log_dir,
                      log_prefix,
                      show_thread=False,
                      **kwargs):
    """Utility function for configuring python logging.
    - log_dir specifies the directory logs will be written to
    - log_prefix is a prefix applied to each file in that directory.
    - if show_thread is True, include the thread name in logs."""
    handler = ClearwaterLogHandler(log_dir, log_prefix)
    log_format = THREAD_FORMAT if show_thread else NO_THREAD_FORMAT
    common_logging(handler, log_level, log_format, **kwargs)

def configure_syslog(log_level, facility=SysLogHandler.LOG_USER, **kwargs):
    """Utility function for sending logs to the local syslog daemon. Users can
    specify the facility the message is sent with.

    Note that a separate rsyslog script will need to be written to write the
    incoming syslog messages to file."""
    handler = SysLogHandler(address="/dev/log", facility=facility)
    common_logging(handler, log_level, NO_TIME_FORMAT, **kwargs)

def common_logging(handler, log_level, log_format, task_id=None):
    if task_id:
        log_prefix += "-{}".format(task_id)

    # Configure the root logger to accept all messages. We control the log
    # level through the handler attached to it (see below).
    root_log = logging.getLogger()
    root_log.setLevel(logging.DEBUG)
    for h in root_log.handlers:
        root_log.removeHandler(h)

    log_format.converter = time.gmtime
    handler.setFormatter(log_format)
    handler.setLevel(log_level)
    root_log.addHandler(handler)

    def exception_logging_handler(type, value, tb): #pragma: no cover
        root_log = logging.getLogger()
        root_log.error("""Uncaught exception:
  Exception: {0}
  Detail: {1}
  Traceback:
  {2}""".format(str(type.__name__),
                str(value),
                "".join(traceback.format_tb(tb))))
        sys.__excepthook__(type, value, tb)

    # Install exception handler
    sys.excepthook = exception_logging_handler


def configure_test_logging():
    """Utility function to configure logging for unit tests.

    If environment variable NOISY is defined, logging will be at debug
    level. Otherwise, it will be at error level.

    If environment variable LOGFILE is defined, logs will be output
    to the named file. Otherwise, they will be sent to stderr.

    This function will remove any previously configured handlers."""
    level = logging.DEBUG if os.getenv('NOISY') else logging.ERROR
    logfile = os.getenv('LOGFILE')

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    for handler in root_logger.handlers:
        root_logger.removeHandler(handler)

    if logfile: #pragma: no cover
        file_handler = logging.FileHandler(logfile)
        file_handler.setLevel(level)
        file_handler.setFormatter(THREAD_FORMAT)
        root_logger.addHandler(file_handler)
    else: #pragma: no cover
        stream_handler = logging.StreamHandler(sys.stderr)
        stream_handler.setLevel(level)
        root_logger.addHandler(stream_handler)
