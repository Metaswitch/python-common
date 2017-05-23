# Copyright (C) Metaswitch Networks 2017
# If license terms are provided to you in a COPYING file in the root directory
# of the source code repository by which you are accessing this code, then
# the license outlined in that COPYING file applies to your use.
# Otherwise no rights are granted except for those provided to you by
# Metaswitch Networks in a separate written agreement.

import syslog

class PDLog(object):
    """Class for defining and making problem determination logs."""
    LOG_NOTICE = syslog.LOG_NOTICE
    LOG_WARNING = syslog.LOG_WARNING
    LOG_ERR = syslog.LOG_ERR

    # The following must be kept in sync with
    # https://github.com/Metaswitch/cpp-common/blob/master/include/pdlog.h
    CL_CPP_COMMON_ID = 1000
    CL_SPROUT_ID = 2000
    CL_CHRONOS_ID = 3000
    CL_HOMESTEAD_ID = 4000
    CL_RALF_ID = 5000
    CL_SCRIPT_ID = 6000
    CL_ASTAIRE_ID = 7000
    CL_CLUSTER_MGR_ID = 8000
    CL_CONFIG_MGR_ID = 9000
    # Range 10000 to 11999 is reserved
    CL_PYTHON_COMMON_ID = 12000
    CL_CREST_ID = 13000
    CL_QUEUE_MGR_ID = 14000
    # Range 15000 to 15999 is reserved
    # Range 16000 to 16999 is reserved
    # Range 17000 to 17999 is reserved
    # Range 18000 to 18999 is reserved
    # Range 19000 to 19999 is reserved

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
