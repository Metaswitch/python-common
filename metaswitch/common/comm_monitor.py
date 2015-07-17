# @file comm_monitor.py
#
# Project Clearwater - IMS in the Cloud
# Copyright (C) 2015 Metaswitch Networks Ltd
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

import logging
from threading import Lock
from alarms import issue_alarm
from monotonic_time import monotonic_time

_log = logging.getLogger(__name__)

class CommunicationMonitor(object):
    def __init__(self, process, raise_identifier, clear_identifier):
        self._process = process
        self._raise_identifier = raise_identifier
        self._clear_identifier = clear_identifier
        self.succeeded = 0
        self.failed = 0
        self.alarmed = False
        self.mutex = Lock()
        self._next_check = 0

    def set_alarm(self):
        self.alarmed = True
        issue_alarm(self._process, self._raise_identifier)

    def clear_alarm(self):
        self.alarmed = False
        issue_alarm(self._process, self._clear_identifier)

    def update_alarm_state(self):
        now = monotonic_time()
        with self.mutex:
            if (now > self._next_check):
                if not self.alarmed:
                    if self.succeeded == 0 and self.failed > 0:
                        self.set_alarm()
                    self._next_check = now + 30
                else:
                    if self.succeeded > 0:
                        self.clear_alarm()
                    self._next_check = now + 15
                self.succeeded = self.failed = 0

    def inform_success(self):
        self.succeeded += 1
        self.update_alarm_state()

    def inform_failure(self):
        self.failed += 1
        self.update_alarm_state()


