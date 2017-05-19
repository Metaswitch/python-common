# @file ifcs.py
#
# Copyright (C) Metaswitch Networks
# If license terms are provided to you in a COPYING file in the root directory
# of the source code repository by which you are accessing this code, then
# the license outlined in that COPYING file applies to your use.
# Otherwise no rights are granted except for those provided to you by
# Metaswitch Networks in a separate written agreement.


def generate_ifcs(domain): #pragma: no cover
    return ('<?xml version="1.0" encoding="UTF-8"?>'
            '<ServiceProfile>'
              '<InitialFilterCriteria>'
                '<TriggerPoint>'
                  '<ConditionTypeCNF>0</ConditionTypeCNF>'
                  '<SPT>'
                    '<ConditionNegated>0</ConditionNegated>'
                    '<Group>0</Group>'
                    '<Method>INVITE</Method>'
                    '<Extension></Extension>'
                  '</SPT>'
                '</TriggerPoint>'
                '<ApplicationServer>'
                  '<ServerName>sip:mmtel.%s</ServerName>'
                  '<DefaultHandling>0</DefaultHandling>'
                '</ApplicationServer>'
              '</InitialFilterCriteria>'
            '</ServiceProfile>') % (domain,)
