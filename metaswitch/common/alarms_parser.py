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
import argparse

# Dictionary of alarm names -> index. Built up by parsing the JSON file
alarm_names = {}

# Valid severity levels - this should be kept in sync with the 
# list in alarmdefinition.h in cpp-common
valid_severity = {"cleared": "1", 
                  "indeterminate": "2", 
                  "critical": "3", 
                  "major": "4", 
                  "minor": "5", 
                  "warning": "6"}

# Valid causes - this should be kept in sync with the
# list in alarmdefinition.h in cpp-common
valid_causes = ["software_error", 
                "database_inconsistency", 
                "underlying_resource_unavailable"]

# Read in the alarms from a JSON file, and write out the alarm IDs
# with their index/severity
def validate_alarms_and_write_constants(json_file, constants_file):

    # Open the JSON file and attempt to parse the JSON
    with open(json_file) as alarms_file:
        alarms = json.load(alarms_file)

    # Parse the JSON file. Each alarm should:
    # - have a cleared alarm and a non-cleared alarm
    # - have a cause that matches an allowed cause
    # - have a severity that matches an allowed severity
    # - have the description/details text be less than 256 characters.
    try:
        for alarm in alarms['alarms']:
            name = alarm['name']
            index = alarm['index']
            assert alarm['cause'].lower() in valid_causes, \
     "Cause ({}) invalid in alarm {}".format(alarm['cause'], name)

            found_cleared = False
            found_non_cleared = False

            for level in alarm['levels']:
                assert len(level['details']) < 256, \
     "Details length was greater than 255 characters in alarm {}".format(name)
                assert len(level['description']) < 256, \
     "Description length was greater than 255 characters in alarm {}".format(name)

                severity = level['severity'].lower()
                assert severity in valid_severity.keys(), \
     "Severity level ({}) invalid in alarm {}".format(level['severity'], name)
                if severity == "cleared":
                    found_cleared = True
                else:
                    found_non_cleared = True

                severity_val = valid_severity[severity]

                # Build up the constants dictionary. When we write to file
                # the constants should have the format:
                #   <ALARM_NAME>_<SEVERITY_NAME> = "<INDEX>_<SEVERITY_INT>"
                alarm_names[name + "_" + severity.upper()] = \
                                       str(index) + "." + severity_val

            # Check that there was a cleared severity level and at least one
            # non-cleared
            assert found_cleared, \
                   "Alarm {} missing a cleared severity".format(name)
            assert found_non_cleared, \
                   "Alarm {} missing any non-cleared severities".format(name)

    except KeyError as e:
        print "Invalid JSON format - missing mandatory value {}".format(e)

    # We've successfully parsed the alarms file. Now write the
    # alarm IDs to file. 
    f = open(constants_file, 'w')    
    for key in alarm_names:
        f.write(key + " = \"" + alarm_names[key] + "\"\n") 
    f.close()

parser = argparse.ArgumentParser()
parser.add_argument('--json-file', type=str, required=True)
parser.add_argument('--constants-file', type=str, required=True)
args = parser.parse_args()

validate_alarms_and_write_constants(args.json_file, args.constants_file)
