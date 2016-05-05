# Project Clearwater - IMS in the Cloud
# Copyright (C) 2016  Metaswitch Networks Ltd
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
import re
import mock
from metaswitch.common.logging_config import (configure_logging,
        configure_test_logging)
import logging

class LoggingTestCase(unittest.TestCase):
    def testLogging(self):
        with mock.patch('os.open') as mock_open:
            configure_logging(logging.DEBUG,
                              ".",
                              "test_log_prefix",
                              task_id="Fred",
                              show_thread=True)

            args, kwargs = mock_open.call_args

            filename_re = "\.\/test_log_prefix-Fred_\d*T\d*Z.txt"
            match = re.compile(filename_re).match(args[0])
            self.assertIsNotNone(match, msg="Unexpected log file name")
            self.assertEqual(args[1], 65, msg="Unexpected log file open flags")
            self.assertEqual(args[2], 420, msg="Unexpected log file open mode")

        # Reset back to the default test logging
        configure_test_logging()

if __name__ == "__main__":
    unittest.main()
