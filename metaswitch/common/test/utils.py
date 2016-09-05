# @file utils.py
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

import logging
import unittest
from metaswitch.common.utils import _HUMAN_SAFE_ALPHABET, _URL_SAFE_ALPHABET, \
    create_secure_mixed_case_human_readable_id
from metaswitch.common.utils import (create_secure_human_readable_id,
                                     create_secure_url_safe_id,
                                     correct_human_readable_id,
                                     encrypt_password,
                                     encrypt_with_blowfish,
                                     decrypt_password,
                                     decrypt_with_blowfish,
                                     hash_password,
                                     is_password_correct,
                                     append_url_params,
                                     sip_uri_to_phone_number,
                                     sip_uri_to_domain,
                                     map_clearwater_log_level,
                                     _pad,
                                     _un_pad)

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

    def testUrlSafeIdDistribution(self):
        """Test that the distribution of the URL-safe ID generator is flat"""
        self.doDistributionTest(create_secure_url_safe_id, _URL_SAFE_ALPHABET)

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

    def testHumanReadableMixedCaseUniqueness(self):
        """Tests that the human-readable ID generator doesn't create duplicates
        over many runs"""
        self.doUniquenessTest(create_secure_mixed_case_human_readable_id)

    def testUrlSafeUniqueness(self):
        """Tests that the URL-safe ID generator doesn't create duplicates
        over many runs"""
        self.doUniquenessTest(create_secure_url_safe_id)

    def testErrorCorrection(self):
        """Tests that the human-readable ID error correction works"""
        self.assertEquals(correct_human_readable_id("ABCabcUu2zZ"),
                          "abcabcvvzzz")

    def test_padding(self):
        self.assertEquals(_pad("", 8), "\x80\x00\x00\x00\x00\x00\x00\x00")
        self.assertEquals(_pad("f", 8), "f\x80\x00\x00\x00\x00\x00\x00")
        self.assertEquals(_pad("fo", 8), "fo\x80\x00\x00\x00\x00\x00")
        self.assertEquals(_pad("foo", 8), "foo\x80\x00\x00\x00\x00")
        self.assertEquals(_pad("foobar", 8), "foobar\x80\x00")
        self.assertEquals(_pad("foobar1", 8), "foobar1\x80")
        self.assertEquals(_pad("foobar12", 8), "foobar12\x80\x00\x00\x00\x00\x00\x00\x00")
        self.assertEquals(_pad("foobar123", 8), "foobar123\x80\x00\x00\x00\x00\x00\x00")

    def test_unpadding(self):
        self.assertEquals(_un_pad("foo\x80\x00\x00\x00"), "foo")
        self.assertEquals(_un_pad("foo\x80"), "foo")
        self.assertRaises(AssertionError, _un_pad, "foo")

    def test_encrypt_with_blowfish(self):
        a = encrypt_with_blowfish("foo", "bar")
        b = encrypt_with_blowfish("foo", "bar")
        self.assertNotEqual(a, b)
        self.assertNotEqual(a, "foo")
        ad = decrypt_with_blowfish(a, "bar")
        bd = decrypt_with_blowfish(b, "bar")
        self.assertEquals(ad, "foo")
        self.assertEquals(bd, "foo")

    def test_encrypt_password(self):
        a = encrypt_password(u"foo", "bar")
        b = encrypt_password(u"foo", "bar")
        self.assertTrue(b[0] == a[0] == 'b')
        self.assertNotEqual(a, b)
        self.assertNotEqual(a, "foo")
        ad = decrypt_password(unicode(a), "bar")
        bd = decrypt_password(b, "bar")
        self.assertEquals(ad, u"foo")
        self.assertEquals(bd, u"foo")
        try:
            bdw = decrypt_password(b, "bar2")
        except:
            # May fail to decode the unicode.
            pass
        else:
            self.assertNotEqual(bdw, "foo")

    def test_hash_password(self):
        def test_password(p):
            hashed = hash_password(p)
            hashed2 = hash_password(p)
            self.assertNotEqual(hashed, hashed2) # Should be salted
            self.assertTrue(is_password_correct(p, hashed))
            self.assertTrue(is_password_correct(p, hashed2))
            self.assertFalse(is_password_correct(p + "a", hashed))
        test_password("foo")
        test_password("bar")
        test_password(u"Smily face \u263A")

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

if __name__ == "__main__":
    unittest.main()
