"""Generate detailed statistics documentation.

This script takes a number of MIB files and merges them with a CSV file
containing additional data, to create an output CSV file suitable for
sharing with RFP central and SAs.

This is not intended to create a document suitable for sharing directly
with customers, but it should make it simple for our customer-facing
teams to make such documents.

An error-level log is output for each:
* Item in the MIB files that doesn't have corresponding extra CSV data.
* Item in the CSV file that can't be found in the MIB files.

To set the logging level, set the LOGGING_LEVEL environemnt variable
to the name of a standard Python logging level e.g. DEBUG.
"""
# To add new fields to the output CSV:
# * Determine where the field comes from and add it to either
#   MibData or CsvData.
# * Enhance `parse_csv_file` or `parse_mib_file` to read the new field.
# * Enhance `merge_entry` to merge the value to the right place
#   in the output CSV.
# * Enhance `COLUMN_HEADERS` to output the new field.
import os
import argparse
import logging
import csv
import StringIO
import sys
import collections
import mib

logger = logging.getLogger(__name__)

# The headers for the output CSV, matching the order in merge_entry
COLUMN_HEADERS = [
    "Version Introduced",
    "MIB Table Name",
    "MIB Field Name",
    "Source File",
    "MIB Table Description",
    "OID",
    "MIB Field Description",
    "Calculation Type",
    "Reset Trigger",
    "Reset Trigger Detail",
    "Data Type",
    "Index Fields",
    "Index Field Values",
    "Field Size",
    "Field Units",
    "Aggregation Mechanism",
]


def merge_entry(key, mib_data, csv_data):
    """Create a tuple in the order specified by COLUMN_HEADERS.

    Inputs are KeyData, MibData and CsvData respectively.
    """
    return (
        csv_data.version_introduced,
        key.mib_table_name,
        key.mib_field_name,
        mib_data.source_file,
        mib_data.mib_table_description,
        mib_data.oid,
        mib_data.mib_field_description,
        csv_data.calculation_type,
        csv_data.reset_trigger,
        csv_data.reset_trigger_detail,
        csv_data.data_type,
        csv_data.index_fields,
        csv_data.index_field_values,
        csv_data.field_size,
        csv_data.field_units,
        csv_data.aggregation_mechanism,
    )

MibData = collections.namedtuple("MibData", ["source_file",
                                             "mib_table_description",
                                             "mib_field_description",
                                             "oid"])
CsvData = collections.namedtuple("CsvData", ["version_introduced",
                                             "calculation_type",
                                             "reset_trigger",
                                             "reset_trigger_detail",
                                             "data_type",
                                             "index_fields",
                                             "index_field_values",
                                             "field_size",
                                             "field_units",
                                             "aggregation_mechanism"])
KeyData = collections.namedtuple("KeyData", ["mib_table_name",
                                             "mib_field_name"])


def main():
    """Main entry point for the script."""
    setup_logging()
    args = parse_args()

    parsed_mibs = parse_mib_files(args['mib_files'])
    try:
        parsed_csv = parse_csv_file(args['csv_file'])
    except IOError:
        sys.exit("Failed to open the CSV file %s." % args['csv_file'])
    merged_entries = merge_csv_with_mibs(parsed_csv, parsed_mibs)

    write_csv(merged_entries, args['output_file'])


def setup_logging():
    """Set up basic logging."""
    # TODO write log level lower than warnings to file if log level set
    # lower than warning.
    level = os.getenv('LOG_LEVEL', 'WARNING')
    logging.basicConfig(level=getattr(logging, level))


def parse_args():
    """Get the command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mib_files', metavar='MIB', nargs='+',
                        help='The absolute path(s) of the input MIB(s).')
    parser.add_argument('csv_file', metavar='CSV',
                        help='The absolute path of the input CSV.')
    parser.add_argument('--output-file', default='./output.csv',
                        help='Optional output file name (defaults to '
                        'output.csv in the current directory).')
    args = vars(parser.parse_args())
    logger.debug("Command-line arguments: %s", args)
    return args


def parse_mib_files(mib_files):
    """Parse the specified MIB files.

    `mib_files` should be an iterator of absolute paths to ASN.1 MIB files on
    disk.
    Returns a dict keyed by (MIB table name, MIB field name) with values
    (Source File, MIB table description, OID, MIB field description).
    If there are any duplicate keys in the provided MIB files, the initial
    value gets overwritten by any occurrence in a MIB file that was provided
    after the MIB file with the first occurrence on the command line.
    """
    output = {}
    for mib_file in mib_files:
        output.update(parse_mib_file(mib_file))
    logging.debug("Parsed MIBs: %s", output)
    return output


def parse_mib_file(path):
    """Parse the specified MIB file.

    `path` should be the absolute path to an ASN.1 MIB file on disk.
    Returns a dict keyed by (MIB table name, MIB field name) with values
    MibData entries.
    """
    mib_file = mib.MibFile(path)

    def stat_test(stat):
        """Filter to determine if this is a statistic nodes

        That's determined by them being leaf nodes, inside a table and not
        indices."""

        # We throw away any fields that
        # - aren't in a table
        # - aren't leaves
        # - are index fields.
        try:
            stat.table()
        except LookupError:
            logger.debug("Stat %s is not in a table - ignoring", stat)
            return False

        # We should just throw away non-leaf nodes but there's no easy way of
        # determining that with the current architecture. Instead we check
        # whether the field finished *Entry which is the only current case of
        # non-leaf MIB fields that aren't indices.
        if stat.get_info("SNMP NAME").endswith("Entry"):
            logger.debug("Stat %s is Entry - ignoring", stat)
            return False

        if stat.is_index_field():
            logger.debug("Stat %s is an index - ignoring", stat)
            return False

        return True

    columns = ["SNMP NAME", "SOURCE FILE", "DESCRIPTION", "OID", ]
    stats = mib_file.get_all_stats(columns).values()

    leaf_stats = [stat for stat in stats if stat_test(stat)]

    def key(stat):
        return KeyData(mib_table_name=stat.table().get_info("SNMP NAME"),
                       mib_field_name=stat.get_info("SNMP NAME"))

    def value(stat):
        return MibData(
            source_file=stat.get_info("SOURCE FILE"),
            mib_table_description=stat.table().get_info("DESCRIPTION"),
            mib_field_description=stat.get_info("DESCRIPTION"),
            oid=stat.get_info("OID"),
        )

    mib_dict = {key(stat): value(stat) for stat in leaf_stats}

    logger.debug("Parsed MIB file, found stats %s", mib_dict)
    return mib_dict


def parse_csv_file(csv_file):
    """Parse the specified CSV file.

    `csv_file` should be an absolute path to a CSV file on disc.
    Returns an OrderedDict keyed by (MIB table name, MIB field name) with
    values CsvData entries.
    """
    with open(csv_file, 'rb') as csvfile:
        reader = csv.DictReader(csvfile)
        rows = list(reader)

    def key(row):
        return KeyData(mib_table_name=row['MIB table name'],
                       mib_field_name=row['MIB field name'])

    def value(row):
        return CsvData(
            version_introduced=row["version introduced"],
            calculation_type=row["calculation type"],
            reset_trigger=row["reset trigger"],
            reset_trigger_detail=row["reset trigger detail"],
            data_type=row["data type"],
            index_fields=row["index fields"],
            index_field_values=row["index field values"],
            field_size=row["field size"],
            field_units=row["field units"],
            aggregation_mechanism=row["aggregation mechanism"],
        )

    parsed_file = collections.OrderedDict((key(row), value(row))
                                          for row in rows)
    logger.debug("Parsed CSV file: %s", parsed_file)

    return parsed_file


def merge_csv_with_mibs(parsed_csv, parsed_mibs):
    """Use the MIBs to complete the information of the CSV.

    Merge dicts on key (MIB table name, MIB field name), keeping order of input
    CSV file.
    Returns list with complete information.
    """
    merged_data = []

    for key, csv_data in parsed_csv.items():
        try:
            mib_data = parsed_mibs.pop(key)
            merged_data.append(merge_entry(key, mib_data, csv_data))
        except KeyError:
            logger.error("Missing MIB value for key %s", key)

    for key in parsed_mibs:
        logger.error("Missing CSV value for key %s", key)

    return merged_data


def write_csv(merged_entries, output_file):
    """Output CSV file to disk.

    `merged_entries` should be a list of data tuples.
    `output_file` should be the path to the output csv.
    """
    logger.info('Generating CSV file %s', output_file)

    output = StringIO.StringIO()
    writer = csv.writer(output, lineterminator='\n')

    writer.writerow(COLUMN_HEADERS)

    for entry in merged_entries:
        writer.writerow(entry)

    with open(output_file, "w") as csv_file:
        csv_file.write(output.getvalue())


if __name__ == "__main__":
    main()
