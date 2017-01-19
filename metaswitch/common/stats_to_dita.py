# Copyright (C) 2016 Metaswitch Networks Ltd. All rights reserved.
'''
A Script to generate DITA documentation of stats from a MIB file.

Required packages:
-SNMP Translate

The script works by taking in a MIB file and running it through SNMP translate to
obtain the details and OID's available. It then builds a dictionary of objects of
class Statistic and then prints out the relevant data as DITA files.   Run with
-h to see the list of necessary parameters.

'''
import subprocess
from collections import defaultdict
import logging
import argparse
import os
import sys
import json
from dita_content import DITAContent

# The column names (written as they are in the MIB file) that are to be
# included.
COLUMNS = ['SNMP NAME', 'OID', 'MAX-ACCESS', 'DESCRIPTION']
COLUMN_WIDTHS = ["38%", "25%", "12%", "25%"]

DEFAULT_OUTPUT_DIR = '.'

white_list = None
black_list = None
ignore_list = []

logging.basicConfig(level=logging.ERROR,
                    format='%(funcName)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Statistic(object):
    ''' The class structure for each OID and its relevant information
    '''

    def __init__(self, oid, mib_file, COLUMNS):
        '''
        Input
        oid:                The specific OID for the statistic
        mib_file:           The location of the MIB file defining the statistic
        COLUMNS:            The properties of the statistic that we want to parse
        '''
        logger.info('Generating an element of class Statistic for OID: %s', oid)

        self.details = {}

        tokenized_details = self._get_tokenized_mib_details(mib_file, oid)

        for item in COLUMNS:
            try:
                item_index = tokenized_details.index(item)
                self.details[item] = tokenized_details[item_index+1]
                if self.details[item][0] == '\"':
                    self.details[item] = self.details[item].strip('\"')
            except:
                self.details[item] = "N/A"

        with open('/dev/null', 'w') as the_bin:
            name = subprocess.check_output('snmptranslate -m ' + mib_file + ' ' +
                                           oid, stderr=the_bin, shell=True)
        # name is in the form  MID_FILE_NAME::snmp name
        self.details['SNMP NAME'] = name.split('::')[1].strip()
        self.details['OID'] = oid.strip()

        logger.debug('generated object of class statistic with OID %s and'
                     ' details %s' % (oid, self.details))

    def get_info(self, name):
        if name in self.details:
            return self.details[name]
        else:
            return False
            logger.warning('could not find a %s for OID %s', name, self.oid)

    def _get_tokenized_mib_details(self, mib_file, oid):
        ''' Gets the details for a statistics from a MIB file.   Splits them by
            whitespace and then regroups anything that is inside {} or "" in
            keeping with ASN1 syntax.

            Input
            mib_file:           The MIB file defining the statistic
            oid:                The OID of the statistic we are interested in
            Return:             A list of tokens, where a token is either a
                                single word or all words enclosed within {} or
                                "".
        '''
        get_details_cmd = 'snmptranslate -m ' + mib_file + ' -Td ' + oid
        with open('/dev/null', 'w') as the_bin:
            detail_string = subprocess.check_output(
                get_details_cmd, stderr=the_bin, shell=True)

        in_quotes = False
        in_braces = False
        output = []
        split_string = detail_string.split()

        for word in split_string:
            if in_quotes or in_braces:
                output[-1] = ' '.join([output[-1], word])
            else:
                output.append(word)

            for character in word:
                if character == '\"':
                    in_quotes = not in_quotes
                elif character == '{' or character == '}':
                    in_braces = not in_braces

        return output


def generate_oid_list(input_file):
    '''Generates a list of OID's from the MIB file

       Input
       location:    location of the current mib file being accessed
    '''
    logger.info('Generating_OID_list from file: %s', input_file)
    with open('/dev/null', 'w') as the_bin:
        oid_string = subprocess.check_output(
            'snmptranslate -m ' + input_file + ' -To', stderr=the_bin, shell=True)
        oid_list = oid_string.split()
    logger.debug('Generated OID list %s', oid_list)
    return oid_list


def get_oids_at_depth(oid_list, depth):
    ''' Generates a list of statistics which are of a given length in the mib

        Input
        oid_list:           A list of the oid's to be checked through, usually
                            from the MIB
        depth:              the relevant depth or length that the OID should be

        Return:             A list of all of the valid OID's
    '''
    logger.info('getting OID\'s at depth %s', depth)
    return filter(lambda oid: len(oid.split('.')) == depth, oid_list)


def write_dita_file(dita_filename, dita_title, table_oids, stats):
    logger.debug('Generating DITA file %s', dita_filename)

    dita_content = DITAContent()
    dita_content.begin_section(dita_title)

    sorted_table_oids = sorted(table_oids)
    for table_oid in sorted_table_oids:
        write_dita_table(stats, table_oid, dita_content)
    dita_content.end_section()

    with open(dita_filename, 'w') as output:
        output.write(dita_content._xml)

def write_dita_table(dictionary, table_oid, dita_content):
    ''' generates a subsection containing a table in the XML

            Input
            dictionary:         A dictionary of OID:statistic(OID)
            table_oid:          The top level OID for the table
            dita_content:       A DITAContent object
    '''
    heads = [word.title() for word in COLUMNS]
    table_name = dictionary[table_oid].get_info('SNMP NAME')

    dita_content.begin_table(table_name, heads, COLUMN_WIDTHS)

    # Loop through the dictionary of all stats finding those that belong to this
    # table.
    for oid in sorted(dictionary):
        stat = dictionary[oid]
        if (oid.startswith(table_oid + '.') or (oid == table_oid)):
            # Here we are certain that an element belongs in our table
            if stat.get_info('DESCRIPTION') == "N/A":
                # This is some kind of intermediate node that isn't of
                # interest.  Skip it.
                continue

            stat_name = stat.get_info('SNMP NAME')
            if not should_output_stat(stat_name):
                continue

            data = [stat.get_info(detail) for detail in COLUMNS]

            dita_content.add_table_entry(data)

    dita_content.end_table()

def should_output_stat(stat_name):
    if (white_list is None) and (black_list is None):
        return True
    if (white_list is not None) and (black_list is not None):
        if (stat_name in white_list) and (stat_name in black_list):
            logger.error("Error: Stat %s is defined in both the whitelist and blacklist" % stat_name)
            sys.exit(1)
        if (stat_name not in white_list) and (stat_name not in black_list):
            logger.error("Error: Stat %s is not defined in either the whitelist or blacklist" % stat_name)
            sys.exit(1)
        return stat_name in white_list
    if (white_list is not None):
        return (stat_name in white_list)
    return (stat_name not in black_list)

if __name__ == '__main__':
    # Do some arg parsing
    parser = argparse.ArgumentParser(
        description='Translates a MIB file for a set of statistics to a set of'
                    ' DITA documents describing them.')
    parser.add_argument('filename', metavar='FILENAME',
                        help='The MIB file you wish to generate your document from')
    parser.add_argument('--oid-base-len', action='store',
                        help='The length of the base OID -- an output file will'
                             ' be generated for each OID with length'
                             ' oid-base-len.   All OIDs with length <'
                             ' oid-base-len will be ignored.')
    parser.add_argument('--output-dir', action='store',
                        help='The directory that the output DITA files should be written to')
    parser.add_argument('--config-file', action='store',
                        help='An optional JSON configuration file defining'
                        ' arrays of top level objects to ignore (ignore_list),'
                        ' individual stats to whitelist (whitelist) and stats'
                        ' to blacklist (blacklist).')
    args = vars(parser.parse_args())

    if args['output_dir']:
        output_dir = args['output_dir']
    else:
        output_dir = DEFAULT_OUTPUT_DIR
    output_name = os.path.join(output_dir, "stats")
    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)

    if args['oid_base_len']:
        oid_base_len = int(args['oid_base_len'])
    else:
        oid_base_len = 0

    input_file = args['filename']

    if args['config_file']:
        with open(args['config_file']) as config_file:
            json_config = json.load(config_file)
            white_list = json_config.get("whitelist", None)
            black_list = json_config.get("blacklist", None)
            ignore_list = json_config.get("ignore_list", [])

    oid_list = generate_oid_list(input_file)

    # Generates a dictionary holding a Statistic for every OID in the OID list
    stats = {}
    for identifier in oid_list:
        stats[identifier] = Statistic(identifier, input_file, COLUMNS)

    # The OIDs at level oid_base_len will become individual output files
    # The OIDs at level oid_base_len+1 will become tables within those output
    # files.
    file_and_table_oids = defaultdict(list)
    table_level_oids = get_oids_at_depth(oid_list, oid_base_len+1)

    for table_oid in table_level_oids:
        top_level_oid = table_oid.rsplit('.', 1)[0]
        top_level_oid_name = stats[top_level_oid].get_info('SNMP NAME')
        if top_level_oid_name not in ignore_list:
            table_oid_name = stats[table_oid].get_info('SNMP NAME')
            if should_output_stat(table_oid_name):
                file_and_table_oids[top_level_oid].append(table_oid)

    for file_oid, table_oids in file_and_table_oids.iteritems():
        file_oid_name = stats[file_oid].get_info('SNMP NAME')
        write_dita_file(output_name + '_' +  file_oid_name + '.xml',
                        file_oid_name,
                        table_oids,
                        stats)
