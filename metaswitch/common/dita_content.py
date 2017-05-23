# Copyright (C) Metaswitch Networks 2017
# If license terms are provided to you in a COPYING file in the root directory
# of the source code repository by which you are accessing this code, then
# the license outlined in that COPYING file applies to your use.
# Otherwise no rights are granted except for those provided to you by
# Metaswitch Networks in a separate written agreement.

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
