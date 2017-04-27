import argparse
import logging
import csv
import StringIO
import collections
import mib

logger = logging.getLogger(__name__)

MibData = collections.namedtuple("MibData", ["source_file",
                                             "mib_table_description",
                                             "oid",
                                             "mib_field_description"])
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


def main():
    setup_logging()
    args = parse_args()

    parsed_mibs = parse_mib_files(args['mib_files'])
    parsed_csv = parse_csv_file(args['csv_file'])

    merged_entries = merge_csv_with_mibs(parsed_csv, parsed_mibs)

    write_csv(merged_entries, args['output_file'])


def setup_logging():
    """Set up basic logging."""
    logging.basicConfig()


def parse_args():
    """Get the command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Generate detailed statistics documentation to be used '
                    'for RFP responses and other customer engagements.')
    parser.add_argument('mib_files', metavar='MIB', nargs='+',
                        help='The absolute path(s) of the input MIB(s).')
    parser.add_argument('csv_file', metavar='CSV',
                        help='The absolute path of the input CSV.')
    parser.add_argument('--output-file', default='./output.csv',
                        help='Optional output file name (defaults to output.csv'
                        ' in the current directory).')
    args = vars(parser.parse_args())
    logger.debug("Command-line arguments: %s", args)
    return args


def parse_mib_files(mib_files):
    """Parse the specified MIB files.

    `mib_files` should be an iterator of absolute paths to ASN.1 MIB files on
    disk.
    Returns a dict keyed by (MIB table name, MIB field name) with values
    (Source File, MIB table description, OID, MIB field description).
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
    all_oids = mib_file.oids

    def stat_test(stat):
        """Filter for leaf nodes in OID tree."""
        oid = stat.get_info("OID")
        depth = len(oid.split('.'))
        # TODO: validate this assumption!
        # TODO: pick the right nodes!
        if depth <= 3:
            return False
        return True

    columns = ["SNMP NAME", "SOURCE FILE", "DESCRIPTION", "OID", ]
    stats = mib_file.get_all_stats(columns).values()

    leaf_stats = [stat for stat in stats if stat_test(stat)]

    def key(stat):
        return (stat.parent().get_info("SNMP NAME"),
                stat.get_info("SNMP NAME"))

    def value(stat):
        return MibData(
            stat.get_info("SOURCE FILE"),
            stat.parent().get_info("DESCRIPTION"),
            stat.get_info("DESCRIPTION"),
            stat.get_info("OID"),
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
        return (row['MIB table name'], row['MIB field name'])

    def value(row):
        return CsvData(
            row["version introduced"],
            row["calculation type"],
            row["reset trigger"],
            row["reset trigger detail"],
            row["data type"],
            row["index fields"],
            row["index field values"],
            row["field size"],
            row["field units"],
            row["aggregation mechanism"],
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
            merged_data.append((
                csv_data.version_introduced,
                key[0],  # MIB Table Name
                mib_data.source_file,
                mib_data.mib_table_description,
                mib_data.oid,
                key[1],  # MIB Field Name
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
            ))
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

    column_headers = [
        "Version Introduced",
        "MIB Table Name",
        "Source File",
        "MIB Table Description",
        "OID",
        "MIB Field Name",
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

    writer.writerow(column_headers)

    for entry in merged_entries:
        writer.writerow(entry)

    with open(output_file, "w") as csv_file:
        csv_file.write(output.getvalue())


if __name__ == "__main__":
    main()
