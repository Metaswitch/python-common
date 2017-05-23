# @file alarm_severities.py
#
# Copyright (C) Metaswitch Networks 2017
# If license terms are provided to you in a COPYING file in the root directory
# of the source code repository by which you are accessing this code, then
# the license outlined in that COPYING file applies to your use.
# Otherwise no rights are granted except for those provided to you by
# Metaswitch Networks in a separate written agreement.

"""
Defines the shared alarm severity definitions used by the package.
"""
# It is not possible to put these in alarms.py as the alarm_parser needs
# access to these, and cannot import alarms as it needs to run too early in
# the build process.

"""
Valid severity levels. This should be kept in sync with the
list in alarmdefinition.h in cpp-common.
Alarms are stored in ITU alarm table using the severities below.
The alarm model table stores alarms according to their state. The
mapping between state and severity is described in RFC 3877
section 5.4: https://tools.ietf.org/html/rfc3877#section-5.4.
"""
CLEARED = 1
INDETERMINATE = 2
CRITICAL = 3
MAJOR = 4
MINOR = 5
WARNING = 6
