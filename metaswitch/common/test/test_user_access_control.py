# Copyright (C) Metaswitch Networks 2017
# If license terms are provided to you in a COPYING file in the root directory
# of the source code repository by which you are accessing this code, then
# the license outlined in that COPYING file applies to your use.
# Otherwise no rights are granted except for those provided to you by
# Metaswitch Networks in a separate written agreement.

import unittest
import re
import mock
import syslog
from metaswitch.common.user_access_control import (audit_log,
                                                   get_user_name)


class UACTestCase(unittest.TestCase):
    """Tests utility functions for user access control."""

    @mock.patch('subprocess.check_output')
    def testGetUserName(self, mock_subprocess):
        """Test that can retrieve get user name."""

        mock_subprocess.return_value = \
            "clearwater      pts/1        2017-10-30 18:25 (:0)"

        user_name = get_user_name()
        self.assertEqual(user_name, "clearwater")

    @mock.patch('os.getenv')
    @mock.patch('subprocess.check_output')
    def testGetUserNameEnv(self, mock_subprocess, mock_getenv):
        """Test that can use env variable for username as fallback."""

        # Return an empty string from the who am i process
        mock_subprocess.return_value = ""
        mock_getenv.return_value = "myusername"

        user_name = get_user_name()
        self.assertEqual(user_name, "myusername")

    @mock.patch('syslog.closelog')
    @mock.patch('syslog.syslog')
    @mock.patch('syslog.openlog')
    def testAuditLog(self, mock_open, mock_syslog, mock_close):
        """Test that audit log happens correctly for various lines."""

        tests = [["Single line",    ["Single line"]],
                 ["Line 1\nLine 2", ["Line 1", "Line 2"]],
                 ["",    []]
                ]

        for test_data in tests:
            test_input = test_data[0]
            test_output = test_data[1]

            audit_log(test_input)

            audit_calls = []
            for test_output_line in test_output:
                audit_calls.append(mock.call(syslog.LOG_NOTICE, test_output_line))

            mock_open.assert_called_once()
            mock_syslog.assert_has_calls(audit_calls)
            mock_close.assert_called_once()

            mock_open.reset_mock()
            mock_syslog.reset_mock()
            mock_close.reset_mock()




