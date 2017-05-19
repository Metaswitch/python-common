# Copyright (C) Metaswitch Networks
# If license terms are provided to you in a COPYING file in the root directory
# of the source code repository by which you are accessing this code, then
# the license outlined in that COPYING file applies to your use.
# Otherwise no rights are granted except for those provided to you by
# Metaswitch Networks in a separate written agreement.

import argparse
from alarms_parser import validate_alarms_and_write_constants

# Wrapper to call alarms parser script with the correct arguments
parser = argparse.ArgumentParser()
parser.add_argument('--json-file', type=str, required=True)
parser.add_argument('--constants-file', type=str, required=True)
args = parser.parse_args()

validate_alarms_and_write_constants(args.json_file, args.constants_file)
