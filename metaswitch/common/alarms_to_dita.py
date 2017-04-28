# Project Clearwater - IMS in the Cloud
# Copyright (C) 2016 Metaswitch Networks Ltd
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

# Simple wrapper to call the write_dita_file script with the correct arguments.

import argparse
import os
import alarms_parser
from dita_content import DITAContent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--alarms-files', nargs="*", type=str, required=True)
    parser.add_argument('--output-dir', type=str, required=True)
    args = parser.parse_args()

    dita_filename = os.path.join('.', args.output_dir, 'alarms.xml')

    write_dita_file(args.alarms_files, dita_filename)


# Read in alarm information from a list of alarms files and write a DITA
# document describing them.
def write_dita_file(alarms_files, dita_filename): #pragma: no cover
    xml = alarms_to_dita(alarms_files)

    with open(dita_filename, "w") as dita_file:
        dita_file.write(xml)


# Read in alarm information from a list of alarms files and generate a DITA
# document describing the alarms.   Returns DITA as XML.
def alarms_to_dita(alarms_files):
    dita_content = DITAContent()
    dita_content.begin_section("Alarms")

    for alarm_file in alarms_files:
        alarm_list = alarms_parser.parse_alarms_file(alarm_file)

        for alarm in alarm_list:
            for alarm_level in alarm._levels.itervalues():
                fields = {"OID": alarms_parser.full_alarm_oid(alarm_level._oid),
                          "ITU severity": alarm_level._itu_severity,
                          "Cause": alarm._cause,
                          "Severity": alarm_level._severity_string,
                          "Description": alarm_level._description,
                          "Details": alarm_level._details,
                          "Cause": alarm_level._cause,
                          "Effect": alarm_level._effect,
                          "Action": alarm_level._action}

                dita_content.begin_table(alarm._name + ": " + alarm_level._severity_string,
                                         ["Field", "Value"],
                                         ["25%", "75%"])
                for field, value in fields.iteritems():
                    dita_content.add_table_entry([field, value])
                dita_content.end_table()

    dita_content.end_section()
    return dita_content._xml


if __name__ == "__main__":
    main()
