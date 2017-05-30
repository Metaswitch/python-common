# @file network_namespace.py
#
# Copyright (C) Metaswitch Networks 2016
# If license terms are provided to you in a COPYING file in the root directory
# of the source code repository by which you are accessing this code, then
# the license outlined in that COPYING file applies to your use.
# Otherwise no rights are granted except for those provided to you by
# Metaswitch Networks in a separate written agreement.

from metaswitch.common._cffi import lib
import socket

def get_signalling_socket(host, port):
    fd = lib.create_connection_in_signaling_namespace(host, str(port))
    if (fd > 0): # pragma: no cover
        return socket.fromfd(fd, socket.AF_UNIX, socket.SOCK_STREAM)
    else:
        return None

