# Project Clearwater - IMS in the Cloud
# Copyright (C) 2015 Metaswitch Networks Ltd
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

import syslog

class PDLog(object):
    """Class for defining and making problem determination logs."""
    LOG_NOTICE = syslog.LOG_NOTICE
    LOG_WARNING = syslog.LOG_WARNING
    LOG_ERR = syslog.LOG_ERR

    # The following must be kept in sync with
    # https://github.com/Metaswitch/cpp-common/blob/dev/include/pdlog.h
    CL_CPP_COMMON_ID = 1000
    CL_SPROUT_ID = 2000
    CL_CHRONOS_ID = 3000
    CL_HOMESTEAD_ID = 4000
    CL_RALF_ID = 5000
    CL_SCRIPT_ID = 6000
    CL_ASTAIRE_ID = 7000
    CL_CLUSTER_MGR_ID = 8000
    CL_CONFIG_MGR_ID = 9000
    # Ranges 10000 to 11999 are reserved
    CL_PYTHON_COMMON_ID = 12000
    CL_CREST_ID = 13000

    def __init__(self, number, desc, cause, effect, action, priority):
        """Defines a particular log's priority and log text.

        The desc, cause, effect and action strings can have named format string
        parameters, which will be filled in when log{} is called.

        The priority must be LOG_NOTICE, LOG_WARNING or LOG_ERR."""
        self._text = ("{} - Description: {} "+
                      "@@Cause: {} "+
                      "@@Effect: {} "+
                      "@@Action: {}").format(number, desc, cause, effect, action)
        self._priority = priority

    def log(self, **kwargs):
        """Logs out the description/cause/effect/action to syslog, including
        named format parameters.

        Note that users should call syslog.openlog before calling this function,
        to set an appropriate process name."""
        syslog.syslog(self._priority, self._text.format(**kwargs))

CASSANDRA_CONNECTION_LOST = PDLog(
    number=PDLog.CL_PYTHON_COMMON_ID + 1,
    desc="The connection to Cassandra has been lost.",
    cause="The connection to Cassandra has been lost.",
    effect="The node can no long offer services that rely on Cassandra.",
    action="(1). Check that Cassandra is running on the node. " +\
      "(2). Check that the configuration files in /etc/clearwater are correct. " +\
      "(3). Check the right ports are open for Cassandra connectivity.",
    priority=PDLog.LOG_ERR)

CASSANDRA_CONNECTION_RECOVERED = PDLog(
    number=PDLog.CL_PYTHON_COMMON_ID + 2,
    desc="The connection to Cassandra has recovered.",
    cause="The connection to Cassandra has recovered.",
    effect="Cassandra backed services are available again.",
    action="None.",
    priority=PDLog.LOG_NOTICE)
