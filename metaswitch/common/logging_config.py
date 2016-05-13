# @file logging_config.py
#
# Project Clearwater - IMS in the Cloud
# Copyright (C) 2013  Metaswitch Networks Ltd
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation, either version 3 of the License, or (at your
# option) any later version, along with the "Special Exception" for use of
# the program along with SSL, set forth below. This program is distributed
# in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details. You should have received a copy of the GNU General Public
# License along with this program.  If not, see
# <http://www.gnu.org/licenses/>.
#
# The author can be reached by email at clearwater@metaswitch.com or by
# post at Metaswitch Networks Ltd, 100 Church St, Enfield EN2 6BQ, UK
#
# Special Exception
# Metaswitch Networks Ltd  grants you permission to copy, modify,
# propagate, and distribute a work formed by combining OpenSSL with The
# Software, or a work derivative of such a combination, even if such
# copying, modification, propagation, or distribution would otherwise
# violate the terms of the GPL. You must comply with the GPL in all
# respects for all of the code used other than OpenSSL.
# "OpenSSL" means OpenSSL toolkit software distributed by the OpenSSL
# Project and licensed under the OpenSSL Licenses, or a work based on such
# software and licensed under the OpenSSL Licenses.
# "OpenSSL Licenses" means the OpenSSL License and Original SSLeay License
# under which the OpenSSL Project distributes the OpenSSL toolkit software,
# as those licenses appear in the file LICENSE-OPENSSL.

import time
import os, sys, traceback
from datetime import datetime
import logging
from logging.handlers import BaseRotatingHandler

# Make the same log formatters available to test code, event though
# it doesn't want to use the full logging config.
THREAD_FORMAT = logging.Formatter('%(asctime)s.%(msecs)03d UTC %(levelname)s %(filename)s:%(lineno)d (thread %(threadName)s): %(message)s', "%d-%m-%Y %H:%M:%S")
NO_THREAD_FORMAT = logging.Formatter('%(asctime)s.%(msecs)03d UTC %(levelname)s %(filename)s:%(lineno)d: %(message)s', "%d-%m-%Y %H:%M:%S")


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
        self.baseFilename = getCurrentFilename(datetime.fromtimestamp(currentTime),
                                               self._log_directory,
                                               self._logfile_prefix)
        self.stream = os.fdopen(os.open(self.baseFilename, os.O_WRONLY | os.O_CREAT, 0644), self.mode)
        self.next_file_change = (int(currentTime / 3600) * 3600) + 3600


def configure_logging(log_level, log_dir, log_prefix, task_id=None, show_thread=False):
    if task_id:
        log_prefix += "-{}".format(task_id)

    # Configure the root logger to accept all messages. We control the log level
    # through the handler attached to it (see below).
    root_log = logging.getLogger()
    root_log.setLevel(logging.DEBUG)
    for h in root_log.handlers:
        root_log.removeHandler(h)

    if show_thread:
        fmt = THREAD_FORMAT
    else: #pragma: no cover
        fmt = NO_THREAD_FORMAT

    fmt.converter = time.gmtime
    handler = ClearwaterLogHandler(log_dir, log_prefix)
    handler.setFormatter(fmt)
    handler.setLevel(log_level)
    root_log.addHandler(handler)

    def exception_logging_handler(type, value, tb): #pragma: no cover
        root_log = logging.getLogger()
        root_log.error("""Uncaught exception:
  Exception: {0}
  Detail: {1}
  Traceback:
  {2}""".format(str(type.__name__), str(value), "".join(traceback.format_tb(tb))))
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
