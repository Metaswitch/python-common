# @file utils.py
#
# Copyright (C) Metaswitch Networks 2015
# If license terms are provided to you in a COPYING file in the root directory
# of the source code repository by which you are accessing this code, then
# the license outlined in that COPYING file applies to your use.
# Otherwise no rights are granted except for those provided to you by
# Metaswitch Networks in a separate written agreement.

import unittest
import mock
from metaswitch.common.pdlogs import PDLog

class PDLogTestCase(unittest.TestCase):
    @mock.patch("syslog.syslog")
    def testLogWithParams(self, mock_syslog):
        TEST_LOG = PDLog(100,
                         desc="This is a test log.",
                         cause="A test has been run.",
                         effect="You will be confident that {acronym} logs work.",
                         action="Check if this test passes.",
                         priority=PDLog.LOG_NOTICE)
        TEST_LOG.log(acronym="ENT")
        expected_text = "100 - Description: This is a test log. @@Cause: A test has been run. "+\
            "@@Effect: You will be confident that ENT logs work. @@Action: Check if this test passes."
        mock_syslog.assert_called_with(PDLog.LOG_NOTICE, expected_text)


    @mock.patch("syslog.syslog")
    def testLogWithoutParams(self, mock_syslog):
        TEST_LOG = PDLog(101,
                         desc="This is a test log.",
                         cause="A test has been run.",
                         effect="You will be confident that PD logs work.",
                         action="Check if this test passes.",
                         priority=PDLog.LOG_NOTICE)
        TEST_LOG.log()
        expected_text = "101 - Description: This is a test log. @@Cause: A test has been run. "+\
            "@@Effect: You will be confident that PD logs work. @@Action: Check if this test passes."
        mock_syslog.assert_called_with(PDLog.LOG_NOTICE, expected_text)
