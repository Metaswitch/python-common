# Copyright (C) Metaswitch Networks 2017
# If license terms are provided to you in a COPYING file in the root directory
# of the source code repository by which you are accessing this code, then
# the license outlined in that COPYING file applies to your use.
# Otherwise no rights are granted except for those provided to you by
# Metaswitch Networks in a separate written agreement.

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
