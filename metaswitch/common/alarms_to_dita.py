# Copyright (C) Metaswitch Networks 2017
# If license terms are provided to you in a COPYING file in the root directory
# of the source code repository by which you are accessing this code, then
# the license outlined in that COPYING file applies to your use.
# Otherwise no rights are granted except for those provided to you by
# Metaswitch Networks in a separate written agreement.

# Simple wrapper to call the write_dita_file script with the correct arguments.

import argparse
import os
from alarms_parser import parse_alarms_file, full_alarm_oid
from dita_content import DITAContent

# Read in alarm information from a list of alarms files and generate a DITA
# document describing the alarms.   Returns DITA as XML.
def alarms_to_dita(alarms_files):
    dita_content = DITAContent()
    dita_content.begin_section("Alarms")

    for alarm_file in alarms_files:
        alarm_list = parse_alarms_file(alarm_file)

        for alarm in alarm_list:
            for alarm_level in alarm._levels.itervalues():
                fields = {"OID": full_alarm_oid(alarm_level._oid),
                          "ITU severity": alarm_level._itu_severity,
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


# Read in alarm information from a list of alarms files and write a DITA
# document describing them.
def write_dita_file(alarms_files, dita_filename): #pragma: no cover
    xml = alarms_to_dita(alarms_files)

    with open(dita_filename, "w") as dita_file:
        dita_file.write(xml)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--alarms-files', nargs="*", type=str, required=True)
    parser.add_argument('--output-dir', type=str, required=True)
    args = parser.parse_args()

    dita_filename = os.path.join('.', args.output_dir, 'alarms.xml')

    write_dita_file(args.alarms_files, dita_filename)
