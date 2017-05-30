# @file throttler.py
#
# Copyright (C) Metaswitch Networks 2013
# If license terms are provided to you in a COPYING file in the root directory
# of the source code repository by which you are accessing this code, then
# the license outlined in that COPYING file applies to your use.
# Otherwise no rights are granted except for those provided to you by
# Metaswitch Networks in a separate written agreement.


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
