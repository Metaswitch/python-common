import argparse
import logging
import mib

logger = logging.getLogger(__name__)


def main():
    setup_logging()
    args = parse_args()

    parsed_mibs = parse_mib_files(args['mib_files'])
    parsed_csv = parse_csv_file(args['csv_file'])

    merged_entries = merge_csv_with_mibs(parsed_csv, parsed_mibs)

    write_csv(merged_entries, args['output_file'])


def setup_logging():
    """Set up basic logging."""
    logging.basicConfig(level=logging.DEBUG)


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
    (Source File, MIB table description, OID, MIB field description).
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
        return (stat.get_info("SOURCE FILE"),
                stat.parent().get_info("DESCRIPTION"),
                stat.get_info("DESCRIPTION"),
                stat.get_info("OID"))

    mib_dict = {key(stat): value(stat) for stat in leaf_stats}

    logger.debug("Parsed MIB file, found stats %s", mib_dict)
    return mib_dict


def parse_csv_file(csv_file):
    """Parse the specified CSV file.

    `csv_file` should be an absolute path to a CSV file on disc.
    Returns an OrderedDict keyed by (MIB table name, MIB field name) with
    values (version introduced,	calculation type, reset trigger,
    reset trigger detail, data type, index fields, index field values,
    field size, field units, aggregation mechanism).
    """
    pass


def merge_csv_with_mibs(parsed_csv, parsed_mibs):
    """Use the MIBs to complete the information of the CSV.

    Merge dicts on key (MIB table name, MIB field name), keeping order of input
    CSV file.
    Returns OrderedDict with complete information.
    """
    pass


def write_csv(merged_entries, output_file):
    """Output CSV file to disk.

    `merged_entries` should be an ordered mapping.
    `output_file` should be the path to the output csv.
    """
    pass


if __name__ == "__main__":
    main()
