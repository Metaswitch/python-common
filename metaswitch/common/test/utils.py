# @file utils.py
#
# Copyright (C) Metaswitch Networks 2016
# If license terms are provided to you in a COPYING file in the root directory
# of the source code repository by which you are accessing this code, then
# the license outlined in that COPYING file applies to your use.
# Otherwise no rights are granted except for those provided to you by
# Metaswitch Networks in a separate written agreement.

import logging
import unittest
from metaswitch.common.utils import (_HUMAN_SAFE_ALPHABET,
                                     create_secure_human_readable_id,
                                     append_url_params,
                                     safely_encode,
                                     sip_uri_to_phone_number,
                                     sip_uri_to_domain,
                                     map_clearwater_log_level)

class UtilsTestCase(unittest.TestCase):
    def doDistributionTest(self, fn, alphabet):
        """
        Tests that the distribution of output characters from the given ID
        generator function is roughly flat.
        """
        dist = {}
        for _ in xrange(1000):
            key = fn(50)
            for c in key:
                if c not in dist:
                    dist[c] = 0
                dist[c] += 1
        total = sum(dist.values())
        for c in alphabet:
            self.assertTrue(dist[c] > total / 2 / len(alphabet))

    def testHumanReadableIdDistribution(self):
        """Test that the distribution of the human-readable ID generator is flat"""
        self.doDistributionTest(create_secure_human_readable_id, _HUMAN_SAFE_ALPHABET)

    def doUniquenessTest(self, fn):
        """Generates a lot of 50-bit IDs and checks that none of them are equal"""
        seen = set()
        for _ in xrange(1000):
            key = fn(50)
            self.assertFalse(key in seen)
            seen.add(key)

    def testHumanReadableUniqueness(self):
        """Tests that the human-readable ID generator doesn't create duplicates
        over many runs"""
        self.doUniquenessTest(create_secure_human_readable_id)

    def test_append_url_params(self):
        self.assertEquals(append_url_params("foo", bar="baz"),
                          "foo?bar=baz")
        self.assertEquals(append_url_params("foo?", bar="baz"),
                          "foo?bar=baz")
        self.assertEquals(append_url_params("foo?bif=bop", bar="baz"),
                          "foo?bif=bop&bar=baz")
        self.assertEquals(append_url_params("foo?bif=bop&", bar="baz"),
                          "foo?bif=bop&bar=baz")
        self.assertEquals(append_url_params("foo?bif=bop&boz", bar="baz"),
                          "foo?bif=bop&boz&bar=baz")
        self.assertEquals(append_url_params("", bar="baz"),
                          "?bar=baz")
        self.assertEquals(append_url_params("foo#bif", bar="baz"),
                          "foo?bar=baz#bif")

    def test_map_clearwater_log_level(self):
        # Error
        self.assertEquals(map_clearwater_log_level(0), logging.ERROR)

        # Warning
        self.assertEquals(map_clearwater_log_level(1), logging.WARNING)

        # Status
        self.assertEquals(map_clearwater_log_level(2, False), logging.WARNING)
        self.assertEquals(map_clearwater_log_level(2, True), logging.INFO)
        self.assertEquals(map_clearwater_log_level(2), logging.INFO)

        # Info
        self.assertEquals(map_clearwater_log_level(3), logging.INFO)

        # Verbose
        self.assertEquals(map_clearwater_log_level(4), logging.DEBUG)

        # Debug
        self.assertEquals(map_clearwater_log_level(5), logging.DEBUG)

        self.assertEquals(map_clearwater_log_level(-1), logging.ERROR)
        self.assertEquals(map_clearwater_log_level(50), logging.DEBUG)

    def test_sip_uri_to_phone_number(self):
        self.assertEquals(sip_uri_to_phone_number("sip:1234@ngv.metaswitch.com"),
                          "1234")

    def test_sip_uri_to_domain(self):
        self.assertEquals(sip_uri_to_domain("sip:1234@abc.ngv.metaswitch.com"),
                          "abc.ngv.metaswitch.com")
        self.assertEquals(sip_uri_to_domain("sip:1234@xyz.ngv.metaswitch.com;gobbledygook"),
                          "xyz.ngv.metaswitch.com")

    def test_safely_encode(self):
        self.assertEquals(safely_encode(None), None)
        self.assertEquals(safely_encode(u'ASCII'), 'ASCII')
        self.assertEquals(safely_encode(u'\x80nonASCII'), '\xc2\x80nonASCII')

if __name__ == "__main__":
    unittest.main()
