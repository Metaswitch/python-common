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

itu_severities = {"cleared": alarm_severities.CLEARED,
                  "indeterminate": alarm_severities.INDETERMINATE,
                  "critical": alarm_severities.CRITICAL,
                  "major": alarm_severities.MAJOR,
                  "minor": alarm_severities.MINOR,
                  "warning": alarm_severities.WARNING}

oid_severities = {"cleared": 1,
                  "indeterminate": 2,
                  "critical": 3,
                  "major": 4,
                  "minor": 5,
                  "warning": 6}

# Valid causes - this should be kept in sync with the
# list in alarmdefinition.h in cpp-common
valid_causes = ["software_error",
                "database_inconsistency",
                "underlying_resource_unavailable"]

class Alarm(object):
    def __init__(self, alarm):
        try:
            self._name = alarm['name']
            self._index = alarm['index']
            self._levels = {}

            assert alarm['cause'].lower() in valid_causes, \
                "Cause ({}) invalid in alarm {}".format(alarm['cause'], self._name)
            self._cause = alarm['cause']

            found_cleared = False
            found_non_cleared = False

            for level in alarm['levels']:
                level_obj = AlarmLevel(self, level)
                self._levels[level_obj._itu_severity] = level_obj

                if level_obj._itu_severity == alarm_severities.CLEARED:
                    found_cleared = True
                else:
                    found_non_cleared = True

            # Check that there was a cleared severity level and at least one
            # non-cleared
            assert found_cleared, \
                   "Alarm {} missing a cleared severity".format(self._name)
            assert found_non_cleared, \
                   "Alarm {} missing any non-cleared severities".format(self._name)

        except KeyError as e:
            print "Invalid JSON format - missing mandatory value {}".format(e)
            raise

class AlarmLevel(object):
    def __init__(self, parent_alarm, level):

        self._parent = parent_alarm
        name = parent_alarm._name

        assert len(level['details']) < 256, \
            "Details length was greater than 255 characters in alarm {}".format(name)
        self._details = level['details']

        assert len(level['description']) < 256, \
            "Description length was greater than 255 characters in alarm {}".format(name)
        self._description = level['description']

        assert len(level['cause']) < 4096, \
            "Cause length was greater than 4096 characters in alarm {}".format(name)
        self._cause = level['cause']

        assert len(level['effect']) < 4096, \
            "Effect length was greater than 4096 characters in alarm {}".format(name)
        self._effect = level['effect']

        assert len(level['action']) < 4096, \
            "Action length was greater than 4096 characters in alarm {}".format(name)
        self._action = level['action']

        # The extended details and extended descriptions fields are
        # optional. We should only check they are under 4096 characters
        # in the case where they exist.
        try:
            assert len(level['extended_details']) < 4096, \
                "Extended details length was greater than 4096 characters in alarm {}".format(name)
            self._details = level['extended_details']
        except KeyError:
            # Valid to not have extended details
            pass

        try:
            assert len(level['extended_description']) < 4096, \
                "Extended description length was greater than 4096 characters in alarm {}".format(name)
            self._description = level['extended_description']
        except KeyError:
            # Valid to not have an extended description
            pass

        severity = level['severity'].lower()
        assert severity in itu_severities.keys(), \
            "Severity level ({}) invalid in alarm {}".format(level['severity'], name)

        self._itu_severity = itu_severities[severity]
        self._oid = self._parent._index + oid_severities[severity]
        self._severity_string = level['severity']


# Read in the alarms from a JSON file, and write out the alarm IDs
# with their index/severity
def parse_alarms_file(json_file):
    # Open the JSON file and attempt to parse the JSON
    with open(json_file) as alarms_file:
        alarms_data = json.load(alarms_file)

    alarms = alarms_data['alarms']

    # List of parsed Alarm objects
    alarm_list = []

    # Parse the JSON file. Each alarm should:
    # - have a cleared alarm and a non-cleared alarm
    # - have a cause that matches an allowed cause
    # - have a severity that matches an allowed severity
    # - have the description/details text be less than 256 characters.
    # - have a more detailed cause text.
    # - have an effect text.
    # - have an action text.
    for alarm in alarms:
        alarm_list.append(Alarm(alarm))

    return alarm_list


def render_alarm(alarm):
    """
    Render an alarm for use in the Python alarm infrastructure.

    Returns a string of format
    `ALARM_NAME = (<index>, <severity1>, <severity2>, ...)`.
    """
    handle_data = [alarm._index]
    handle_data.extend(alarm._levels.keys())
    return '{} = {}\n'.format(alarm._name.upper(),
                              tuple(handle_data))


def write_constants_file(alarm_details, constants_file): # pragma: no cover
    # We've successfully parsed the alarms file. Now write the
    # alarm IDs to file.
    f = open(constants_file, 'w')
    for alarm in alarm_details:
        f.write(render_alarm(alarm))
    f.close()


# Read in the alarms from a JSON file, and write out the alarm IDs
# with their index/severity
def validate_alarms_and_write_constants(json_file, constants_file): # pragma: no cover
    alarm_list = parse_alarms_file(json_file)
    write_constants_file(alarm_list, constants_file)

def alarms_to_dita(title, alarms):
    columns = ["OID",
               "ITU_severity",
               "name",
               "cause",
               "severity",
               "description",
               "details",
               "cause",
               "effect",
               "action"]

    writer = DITATableWriter()
    writer.begin_section(title)
    writer.begin_table("Alarm definitions", columns)
    for alarm in alarms:
        for alarm_level in alarm._levels.itervalues():
            writer.add_table_entry([alarm_level._oid,
                                    alarm_level._itu_severity,
                                    alarm._name,
                                    alarm._cause,
                                    alarm_level._severity_string,
                                    alarm_level._description,
                                    alarm_level._details,
                                    alarm_level._cause,
                                    alarm_level._effect,
                                    alarm_level._action])
    writer.end_table()
    writer.end_section()
    return writer._xml

def write_alarm_dita_doc(json_file, dita_file):
    alarm_list = parse_alarms_file(json_file)
    xml = alarms_to_dita(json_file, alarm_list)

    with open(dita_file, "w") as output_file:
        output_file.write(xml)

class DITATableWriter(object):
    def __init__(self):
        self._xml = ""

    def begin_section(self, doc_title):
        self._xml += '<?xml version="1.0" encoding="UTF-8"?>\n'
        self._xml += '<!DOCTYPE concept PUBLIC "-//OASIS//DTD DITA Concept//EN" "concept.dtd">\n'
        self._xml += '<concept id="concept_tdn_k5t_vw">\n'
        self._xml += '<title>' + doc_title + '</title>\n'
        self._xml += '<conbody>\n'

    def begin_table(self, title, columns):
        self._columns = columns
        self._xml += '<p>\n'
        self._xml += '<table frame="all" rowsep="1" colsep="1" id="table_sqg_l5t_vw">\n'
        self._xml += '<title>' + title + '</title>\n'
        self._xml += '<tgroup cols="' + str(len(columns)) + '">\n'

        for index, column in enumerate(columns, start=1):
            self._xml += '<colspec colname="c' + str(index) + '" colnum="' + str(index) + '" colwidth="1.0*"/>\n'

        self._xml += '<thead>\n'
        self._xml += '<row>\n'
        for column in columns:
            self._xml += '<entry>\n<p>' + column + '</p>\n</entry>\n'
        self._xml += '</row>\n'
        self._xml += '</thead>\n'
        self._xml += '<tbody>\n'

    def end_table(self):
        self._xml += '</tbody>\n'
        self._xml += '</tgroup>\n'
        self._xml += '</table>\n'
        self._xml += '</p>\n'

    def end_section(self):
        self._xml += '</conbody>\n'
        self._xml += '</concept>\n'

    def add_table_entry(self, data):
        self._xml += '<row>\n'
        for value in data:
            self._xml += '<entry>\n<p>' + str(value) + '</p>\n</entry>\n'
        self._xml += '</row>\n'
