# Project Clearwater - IMS in the Cloud
# Copyright (C) 2015  Metaswitch Networks Ltd
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
from metaswitch.common.alarms import CLEARED, CRITICAL
from metaswitch.common.alarms_parser import parse_alarms_file, render_alarm

class AlarmsParserTestCase(unittest.TestCase):
    def testValidFile(self):
        alarms = parse_alarms_file('metaswitch/common/test/test_valid_alarms.json')
        test_alarm = alarms[0]
        self.assertEqual(test_alarm[0], 'NAME', msg="Incorrect name.")
        self.assertEqual(test_alarm[1], 1000, msg="Incorrect index.")
        self.assertIn(CLEARED, test_alarm[2], msg="No cleared state.")
        self.assertIn(CRITICAL, test_alarm[2], msg="No critical state.")

    def testInvalidCause(self):
        self.assertRaisesRegexp(AssertionError,
                                "Cause \(NOT_CAUSE\) invalid in alarm NAME",
                                parse_alarms_file,
                                'metaswitch/common/test/test_invalid_cause.json')

    def testMissingNonClearedAlarm(self):
        self.assertRaisesRegexp(AssertionError,
                                "Alarm NAME missing any non-cleared severities",
                                parse_alarms_file,
                                'metaswitch/common/test/test_missing_non_cleared.json')

    def testMissingMandatoryValue(self):
        self.assertRaisesRegexp(KeyError,
                                "'severity'",
                                parse_alarms_file,
                                'metaswitch/common/test/test_missing_severity_value.json')
        self.assertRaisesRegexp(KeyError,
                                "'cause'",
                                parse_alarms_file,
                                'metaswitch/common/test/test_missing_cause_value.json')
        self.assertRaisesRegexp(KeyError,
                                "'effect'",
                                parse_alarms_file,
                                'metaswitch/common/test/test_missing_effect_value.json')
        self.assertRaisesRegexp(KeyError,
                                "'action'",
                                parse_alarms_file,
                                'metaswitch/common/test/test_missing_action_value.json')

    def testRenderSimpleAlarm(self):
        """Check that a single-severity alarm can be rendered."""
        self.assertEqual(render_alarm('Dummy_error', 1000, (1, 3)),
                         'DUMMY_ERROR = (1000, 1, 3)\n')

    def testRenderMultiAlarm(self):
        """Check that a multi-severity alarm can be rendered."""
        self.assertEqual(render_alarm('dummy_3rror', 1000, (1, 3, 6)),
                         'DUMMY_3RROR = (1000, 1, 3, 6)\n')

if __name__ == "__main__":
    unittest.main()
