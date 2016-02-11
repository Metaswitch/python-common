# @file throttler.py
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


import unittest
import mock

from metaswitch.common.comm_monitor import CommunicationMonitor
from metaswitch.common.pdlogs import CASSANDRA_CONNECTION_LOST, CASSANDRA_CONNECTION_RECOVERED

class CMTestCase(unittest.TestCase):
    @mock.patch("metaswitch.common.comm_monitor.alarm_manager")
    @mock.patch("metaswitch.common.comm_monitor.monotonic_time")
    def test_simple(self, mock_time, mock_alarm_manager):
        """Simple test of basic behaviour."""

        mock_alarm = mock_alarm_manager.get_alarm.return_value
        cm = CommunicationMonitor("ut", "1000.3", CASSANDRA_CONNECTION_LOST, CASSANDRA_CONNECTION_RECOVERED)
        mock_alarm_manager.get_alarm.assert_called_with("ut", "1000.3")

        # Move time forwards and report a failure. We should raise an alarm.
        mock_time.return_value = 1000
        cm.inform_failure()
        mock_alarm.set.assert_called_once_with()

        # Move time forwards and report a success. We should clear that alarm.
        mock_time.return_value = 3000
        cm.inform_success()
        mock_alarm.clear.assert_called_with()



if __name__ == "__main__":
    unittest.main()
