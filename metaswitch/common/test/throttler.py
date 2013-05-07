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
import time

from metaswitch.common.throttler import Throttler

# Rate to use in testing (per second).  Tradeoff between speed of test
# and probability of spurious failures.
RATE = 10
DELAY = 1.0/RATE

class ThrottlerTestCase(unittest.TestCase):
    def test_simple(self):
        """Simple test of basic behaviour."""
        throttler = Throttler(RATE, 5)
        self.assertEquals(True, throttler.is_allowed())
        self.assertEquals(True, throttler.is_allowed())
        self.assertEquals(True, throttler.is_allowed())
        self.assertEquals(True, throttler.is_allowed())
        self.assertEquals(True, throttler.is_allowed())
        self.assertEquals(False, throttler.is_allowed())
        self.assertEquals(False, throttler.is_allowed())
        time.sleep(DELAY * 1.1)
        self.assertEquals(True, throttler.is_allowed())
        self.assertEquals(False, throttler.is_allowed())
        time.sleep(DELAY * 7)
        self.assertEquals(True, throttler.is_allowed())
        self.assertEquals(True, throttler.is_allowed())
        self.assertEquals(True, throttler.is_allowed())
        self.assertEquals(True, throttler.is_allowed())
        self.assertEquals(True, throttler.is_allowed())
        self.assertEquals(False, throttler.is_allowed())

    def test_interval(self):
        throttler = Throttler(0.02, 5)
        self.assertEquals(50, throttler.interval_sec)

    def test_interval_clip(self):
        throttler = Throttler(10, 5)
        self.assertEquals(1, throttler.interval_sec)

if __name__ == "__main__":
    unittest.main()
