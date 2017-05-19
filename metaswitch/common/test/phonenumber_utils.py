# Copyright (C) Metaswitch Networks
# If license terms are provided to you in a COPYING file in the root directory
# of the source code repository by which you are accessing this code, then
# the license outlined in that COPYING file applies to your use.
# Otherwise no rights are granted except for those provided to you by
# Metaswitch Networks in a separate written agreement.

import unittest
from metaswitch.common.phonenumber_utils import format_phone_number

class PhonenumberUtilTestCase(unittest.TestCase):
    def testValidUSDN(self):
        number = format_phone_number('+1 415 513-1500')
        self.assertEqual(number, '(415) 513-1500', msg="Incorrect number format")

    def testInvalidUSDN(self):
        number = format_phone_number('+991 415 513-1500')
        self.assertEqual(number, '+991 415 513-1500', msg="Failed to return original number on error")

if __name__ == "__main__":
    unittest.main()
