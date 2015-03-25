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
from tornado import ioloop
import threading
import traceback

_log = logging.getLogger("metaswitch.utils")

_main_thread = None
_thread_violation = False

def assert_main_thread():
    global _main_thread
    global _thread_violation
    my_thread = threading.current_thread().ident
    if _main_thread is not None:
        if my_thread != _main_thread:
            try:
                _thread_violation = True
                raise AssertionError("This function should only be called from the main thread")
            except:
                _log.exception("This function should only be called form the main thread")
                raise
    else:
        # We don't know what the main thread is yet.  Queue up an action on
        # the main thread to save it off and then check this thread was
        # correct.
        my_stack = traceback.format_stack()
        def _set_main_thread():
            global _main_thread
            global _thread_violation
            _main_thread = threading.current_thread().ident
            if my_thread != _main_thread:
                _thread_violation = True
                raise AssertionError("This function should only be called "
                                     "from the main thread.  Original stack:\n" +
                                     "".join(my_stack))
        ioloop.IOLoop.instance().add_callback(_set_main_thread)

