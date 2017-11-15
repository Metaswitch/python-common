# @file logging_config.py
#
# Copyright (C) Metaswitch Networks 2017
# If license terms are provided to you in a COPYING file in the root directory
# of the source code repository by which you are accessing this code, then
# the license outlined in that COPYING file applies to your use.
# Otherwise no rights are granted except for those provided to you by
# Metaswitch Networks in a separate written agreement.
import syslog
import subprocess
import os

def get_user_name():
    """
    Returns the local user name if no RADIUS server was used and returns the
    user name that was used to authenticate with a RADIUS server, if used.
    Note that this only works if called from the terminal.
    """
    # Worth noting that `whoami` behaves differently to `who am i`, we need the
    # latter.
    process = subprocess.check_output(["who", "am", "i"])
    splits = process.split()
    if splits:
        # The format of `who am i` looks like this:
        #
        # clearwater      pts/1        2017-10-30 18:25 (:0)
        #
        # This is the login that is associated with the current user.
        return splits[0]
    else:
        # `who am i` has not returned anything! This happens if the connection
        # has been made via the console rather than over ssh. In these
        # situations, we can use the $USER environment variable as a backup.
        return os.getenv("USER")

def audit_log (msg):
    """Make an audit syslog, splitting up the request as required to prevent it
    being dropped or truncated"""

    lines = msg.split("\n")

    syslog.openlog("audit-log", syslog.LOG_PID, facility=syslog.LOG_AUTH)

    for line in lines:
        syslog.syslog(syslog.LOG_NOTICE, line.encode("utf-8"))

    syslog.closelog()

