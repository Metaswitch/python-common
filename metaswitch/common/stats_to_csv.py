# Copyright (C) 2016 Metaswitch Networks Ltd. All rights reserved.
'''
A Script to generate CSV documentation of alarms from a JSON file.

Required packages:
-SNMP Translate

@TODO

'''

import StringIO
import csv
import logging
import argparse
import os
import json
from collections import defaultdict
from stats_to_dita import (
          Statistic, generate_oid_list, get_oids_at_depth, should_output_stat)

COLUMNS = ['SNMP NAME', 'OID', 'MAX-ACCESS', 'DESCRIPTION']

DEFAULT_OUTPUT_DIR = '.'

white_list = None
black_list = None
ignore_list = []

logging.basicConfig(level=logging.ERROR,
                    format='%(funcName)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def write_csv_file(csv_filename, table_oids, stats):
    logger.debug('Generating CSV file %s', csv_filename)

    output = StringIO.StringIO()
    writer = csv.writer(output, lineterminator='\n')

    writer.writerow(COLUMNS)

    sorted_table_oids = sorted(table_oids)
    for table_oid in sorted_table_oids:
        for oid in sorted(stats):
            stat = stats[oid]
            if (oid.startswith(table_oid + '.') or (oid == table_oid)):
                if stat.get_info('DESCRIPTION') == "N/A":
                    # This is some kind of intermediate node that isn't of
                    # interest.  Skip it.
                    continue

                stat_name = stat.get_info('SNMP NAME')
                if not should_output_stat(stat_name):
                    continue

                data = [stat.get_info(detail) for detail in COLUMNS]

                writer.writerow(data)

    with open(csv_filename, "w") as csv_file:
        csv_file.write(output.getvalue())


if __name__ == '__main__':
    # Do some arg parsing
    parser = argparse.ArgumentParser(
        description='Translates a MIB file for a set of statistics to a set of'
                    ' CSV documents describing them.')
    parser.add_argument(
        'filename',
        metavar='FILENAME',
        help='The MIB file you wish to generate your document from')
    parser.add_argument(
        '--oid-base-len',
        action='store',
        help='The length of the base OID -- an output file will'
             ' be generated for each OID with length'
             ' oid-base-len.   All OIDs with length <'
             ' oid-base-len will be ignored.')
    parser.add_argument(
        '--output-dir',
        action='store',
        help='The directory that the output CSV files should be written to')
    parser.add_argument(
        '--config-file',
        action='store',
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
        write_csv_file(output_name + '_' + file_oid_name + '.xml',
                       table_oids,
                       stats)
