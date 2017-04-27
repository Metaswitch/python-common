import argparse
import logging

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
    pass


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
