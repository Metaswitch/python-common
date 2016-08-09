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

import json
import alarm_severities

# Valid severity levels - this should be kept in sync with the
# list in alarmdefinition.h in cpp-common
# Alarms are stored in ITU Alarm Table using the severities below.
# Alarm Model Table stores alarms according to their state. The
# mapping between state and severity is described in RFC 3877
# section 5.4: https://tools.ietf.org/html/rfc3877#section-5.4
# The function AlarmTableDef::state() maps severities to states.

valid_severity = {"cleared": alarm_severities.CLEARED,
                  "indeterminate": alarm_severities.INDETERMINATE,
                  "critical": alarm_severities.CRITICAL,
                  "major": alarm_severities.MAJOR,
                  "minor": alarm_severities.MINOR,
                  "warning": alarm_severities.WARNING}

# Valid causes - this should be kept in sync with the
# list in alarmdefinition.h in cpp-common
valid_causes = ["software_error",
                "database_inconsistency",
                "underlying_resource_unavailable"]


# Read in the alarms from a JSON file, and write out the alarm IDs
# with their index/severity
def parse_alarms_file(json_file):
    # Open the JSON file and attempt to parse the JSON
    with open(json_file) as alarms_file:
        alarms_data = json.load(alarms_file)

    alarms = alarms_data['alarms']

    # Dictionary of alarm names -> index. Built up by parsing the JSON file
    alarm_details = []

    # Parse the JSON file. Each alarm should:
    # - have a cleared alarm and a non-cleared alarm
    # - have a cause that matches an allowed cause
    # - have a severity that matches an allowed severity
    # - have the description/details text be less than 256 characters.
    # - have a more detailed cause text.
    # - have an effect text.
    # - have an action text.
    try:
        for alarm in alarms:
            name = alarm['name']
            index = alarm['index']
            severities = []

            assert alarm['cause'].lower() in valid_causes, \
     "Cause ({}) invalid in alarm {}".format(alarm['cause'], name)

            found_cleared = False
            found_non_cleared = False

            for level in alarm['levels']:
                assert len(level['details']) < 256, \
     "Details length was greater than 255 characters in alarm {}".format(name)
                assert len(level['description']) < 256, \
     "Description length was greater than 255 characters in alarm {}".format(name)
                assert len(level['cause']) < 4096, \
     "Cause length was greater than 4096 characters in alarm {}".format(name)
                assert len(level['effect']) < 4096, \
     "Effect length was greater than 4096 characters in alarm {}".format(name)
                assert len(level['action']) < 4096, \
     "Action length was greater than 4096 characters in alarm {}".format(name)
                
                # The extended details and extended descriptions fields are
                # optional. We should only check they are under 4096 characters
                # in the case where they exist.
                try:
                    assert len(level['extended_details']) < 4096, \
        "Extended details length was greater than 4096 characters in alarm {}".format(name)
                except KeyError:
                    # Valid to not have extended details
                    pass
                    
                try:
                    assert len(level['extended_description']) < 4096, \
        "Extended description length was greater than 4096 characters in alarm {}".format(name)
                except KeyError:
                    # Valid to not have an extended description
                    pass

                severity = level['severity'].lower()
                assert severity in valid_severity.keys(), \
     "Severity level ({}) invalid in alarm {}".format(level['severity'], name)
                if severity == "cleared":
                    found_cleared = True
                else:
                    found_non_cleared = True

                severities.append(valid_severity[severity])

            # Check that there was a cleared severity level and at least one
            # non-cleared
            assert found_cleared, \
                   "Alarm {} missing a cleared severity".format(name)
            assert found_non_cleared, \
                   "Alarm {} missing any non-cleared severities".format(name)

            alarm_details.append((name, index, severities))

    except KeyError as e:
        print "Invalid JSON format - missing mandatory value {}".format(e)
        raise

    return alarm_details


def render_alarm(name, index, severities):
    """
    Render an alarm for use in the Python alarm infrastructure.

    Returns a string of format
    `ALARM_NAME = (<index>, <severity1>, <severity2>, ...)`.
    """
    handle_data = [index]
    handle_data.extend(severities)
    return '{} = {}\n'.format(name.upper(),
                              tuple(handle_data))


def write_constants_file(alarm_details, constants_file): # pragma: no cover
    # We've successfully parsed the alarms file. Now write the
    # alarm IDs to file.
    f = open(constants_file, 'w')
    for (name, index, severities) in alarm_details:
        f.write(render_alarm(name, index, severities))
    f.close()


# Read in the alarms from a JSON file, and write out the alarm IDs
# with their index/severity
def validate_alarms_and_write_constants(json_file, constants_file): # pragma: no cover
    alarm_details = parse_alarms_file(json_file)
    write_constants_file(alarm_details, constants_file)
