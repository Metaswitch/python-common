# @file utils.py
#
# Copyright (C) Metaswitch Networks
# If license terms are provided to you in a COPYING file in the root directory
# of the source code repository by which you are accessing this code, then
# the license outlined in that COPYING file applies to your use.
# Otherwise no rights are granted except for those provided to you by
# Metaswitch Networks in a separate written agreement.

import unittest
from metaswitch.common import network_namespace

class NetworkNamespaceTestCase(unittest.TestCase):

    # Test that we can call get_signalling_socket (and that it fails, returning
    # None). This is largely a test that all the CFFI infrastructure is in
    # place.
    def test_netns(self):
        self.assertEquals(network_namespace.get_signalling_socket("localhost", 9000),
                          None)
