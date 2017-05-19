# Copyright (C) Metaswitch Networks
# If license terms are provided to you in a COPYING file in the root directory
# of the source code repository by which you are accessing this code, then
# the license outlined in that COPYING file applies to your use.
# Otherwise no rights are granted except for those provided to you by
# Metaswitch Networks in a separate written agreement.

import phonenumbers

def format_phone_number(number):
    try:
        # TODO support non-US
        numobj = phonenumbers.parse(number, "US")
        number = phonenumbers.format_number(numobj,
                                            phonenumbers.PhoneNumberFormat.NATIONAL)
    except Exception:
        return number
    return number

