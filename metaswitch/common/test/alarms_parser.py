# Copyright (C) Metaswitch Networks 2016
# If license terms are provided to you in a COPYING file in the root directory
# of the source code repository by which you are accessing this code, then
# the license outlined in that COPYING file applies to your use.
# Otherwise no rights are granted except for those provided to you by
# Metaswitch Networks in a separate written agreement.

import unittest
from metaswitch.common.alarms import CLEARED, CRITICAL
from metaswitch.common.alarms_parser import parse_alarms_file, render_alarm, alarms_to_dita, alarms_to_csv

class AlarmsParserTestCase(unittest.TestCase):
    def testValidFile(self):
        alarms = parse_alarms_file('metaswitch/common/test/test_valid_alarms.json')
        test_alarm = alarms[0]
        self.assertEqual(test_alarm._name, 'NAME', msg="Incorrect name.")
        self.assertEqual(test_alarm._index, 1000, msg="Incorrect index.")
        self.assertIn(CLEARED, test_alarm._levels.keys(), msg="No cleared state.")
        self.assertIn(CRITICAL, test_alarm._levels.keys(), msg="No critical state.")

    def testRenderAlarm(self):
        alarms = parse_alarms_file('metaswitch/common/test/test_valid_alarms.json')
        test_alarm = alarms[0]
        self.assertEqual(render_alarm(test_alarm), 'NAME = (1000, 1, 3)\n')

    def testDita(self):
        expected_output = open('metaswitch/common/test/test_valid_alarms.dita').read()
        self.assertEqual(alarms_to_dita(["metaswitch/common/test/test_valid_alarms.json"]),
                         expected_output)

    def testCsv(self):
        expected_output = open('metaswitch/common/test/test_valid_alarms.csv').read()
        self.assertEqual(alarms_to_csv(["metaswitch/common/test/test_valid_alarms.json"]),
                         expected_output)

    def testDetailsTooLong(self):
        self.assertRaisesRegexp(AssertionError,
                                "Details length was greater than 255 characters in alarm NAME",
                                parse_alarms_file,
                                'metaswitch/common/test/details_too_long.json')

    def testDescriptionTooLong(self):
        self.assertRaisesRegexp(AssertionError,
                                "Description length was greater than 255 characters in alarm NAME",
                                parse_alarms_file,
                                'metaswitch/common/test/desc_too_long.json')

    def testCauseTooLong(self):
        self.assertRaisesRegexp(AssertionError,
                                "Cause length was greater than 4096 characters in alarm NAME",
                                parse_alarms_file,
                                'metaswitch/common/test/cause_too_long.json')

    def testEffectTooLong(self):
        self.assertRaisesRegexp(AssertionError,
                                "Effect length was greater than 4096 characters in alarm NAME",
                                parse_alarms_file,
                                'metaswitch/common/test/effect_too_long.json')

    def testActionTooLong(self):
        self.assertRaisesRegexp(AssertionError,
                                "Action length was greater than 4096 characters in alarm NAME",
                                parse_alarms_file,
                                'metaswitch/common/test/action_too_long.json')

    def testExtendedDetailsTooLong(self):
        self.assertRaisesRegexp(AssertionError,
                                "Extended details length was greater than 4096 characters in alarm NAME",
                                parse_alarms_file,
                                'metaswitch/common/test/extended_details_too_long.json')

    def testExtendedDescriptionTooLong(self):
        self.assertRaisesRegexp(AssertionError,
                                "Extended description length was greater than 4096 characters in alarm NAME",
                                parse_alarms_file,
                                'metaswitch/common/test/extended_description_too_long.json')
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


if __name__ == "__main__":
    unittest.main()
