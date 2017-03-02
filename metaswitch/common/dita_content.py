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

# Class that constructs the content of a DITA file consisting of a number of
# simple tables.  For an example of a DITA file constructed using this class,
# see test/test_valid_alarms.dita.

DOCTYPE_TAG = ('<!DOCTYPE concept PUBLIC "-//OASIS//DTD DITA Concept//EN" '
               '"concept.dtd">\n')
COLSPEC_TAG = '<colspec colname="c{0!s}" colnum="{1!s}" colwidth="{2}"/>\n'


class DITAContent(object):
    def __init__(self):
        self._xml = ""

    def begin_section(self, doc_title):
        self._xml += '<?xml version="1.0" encoding="UTF-8"?>\n'
        self._xml += DOCTYPE_TAG
        self._xml += '<concept>\n'
        self._xml += '<title>' + doc_title + '</title>\n'
        self._xml += '<conbody>\n'

    def begin_table(self, title, columns, widths):
        self._xml += '<table frame="all" rowsep="1" colsep="1">\n'
        self._xml += '<title>' + title + '</title>\n'
        self._xml += '<tgroup cols="' + str(len(columns)) + '">\n'

        for index, column in enumerate(columns, start=1):
            self._xml += COLSPEC_TAG.format(index, index, widths[index - 1])

        self._xml += '<thead>\n'
        self._xml += '<row>\n'
        for column in columns:
            self._xml += '<entry>\n<p><b>' + column + '</b></p>\n</entry>\n'
        self._xml += '</row>\n'
        self._xml += '</thead>\n'
        self._xml += '<tbody>\n'

    def end_table(self):
        self._xml += '</tbody>\n'
        self._xml += '</tgroup>\n'
        self._xml += '</table>\n'

    def end_section(self):
        self._xml += '</conbody>\n'
        self._xml += '</concept>\n'

    def add_table_entry(self, data):
        self._xml += '<row>\n'
        for value in data:
            self._xml += '<entry>\n<p>' + str(value) + '</p>\n</entry>\n'
        self._xml += '</row>\n'
