# Copyright (C) Metaswitch Networks 2017
# If license terms are provided to you in a COPYING file in the root directory
# of the source code repository by which you are accessing this code, then
# the license outlined in that COPYING file applies to your use.
# Otherwise no rights are granted except for those provided to you by
# Metaswitch Networks in a separate written agreement.

import unittest
import re
import logging
import mock
from metaswitch.common.logging_config import (configure_logging,
                                              configure_test_logging,
                                              configure_syslog)


class LoggingTestCase(unittest.TestCase):
    """Tests utility functions for setting up logging."""

    def tearDown(self):
        # Once these tests are finished, we want to reset to using standard
        # test logging.
        configure_test_logging()

    @mock.patch('os.open')
    def testLogging(self, mock_open):
        """Test that configure_logging() will result in writing to file."""
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

    @mock.patch('metaswitch.common.logging_config.SysLogHandler',
                autospec=True)
    def test_syslog(self, mock_syslog):
        """Test that messages are logged to syslog."""
        configure_syslog(logging.DEBUG)
        mock_syslog.return_value.level = logging.DEBUG
        log = logging.getLogger()
        log.info("Try writing a log")

        self.assertTrue(mock_syslog.return_value.handle.called)


if __name__ == "__main__":
    unittest.main()
