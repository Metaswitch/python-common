# Copyright (C) Metaswitch Networks 2017
# If license terms are provided to you in a COPYING file in the root directory
# of the source code repository by which you are accessing this code, then
# the license outlined in that COPYING file applies to your use.
# Otherwise no rights are granted except for those provided to you by
# Metaswitch Networks in a separate written agreement.

# Simple wrapper to call the write_csv_file script with the correct arguments.

import argparse
import os
from alarms_parser import write_csv_file

parser = argparse.ArgumentParser()
parser.add_argument('--alarms-files', nargs="*", type=str, required=True)
parser.add_argument('--output-dir', type=str, required=True)
args = parser.parse_args()

csv_filename = os.path.join('.', args.output_dir, 'alarms.csv')

write_csv_file(args.alarms_files, csv_filename)

