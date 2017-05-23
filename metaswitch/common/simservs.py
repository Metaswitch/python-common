# @file simservs.py
#
# Copyright (C) Metaswitch Networks 2017
# If license terms are provided to you in a COPYING file in the root directory
# of the source code repository by which you are accessing this code, then
# the license outlined in that COPYING file applies to your use.
# Otherwise no rights are granted except for those provided to you by
# Metaswitch Networks in a separate written agreement.

def default_simservs(): #pragma: no cover
    return """<?xml version="1.0" encoding="UTF-8"?><simservs xmlns="http://uri.etsi.org/ngn/params/xml/simservs/xcap" xmlns:cp="urn:ietf:params:xml:ns:common-policy"><originating-identity-presentation active="true"/><originating-identity-presentation-restriction active="true"><default-behaviour>presentation-not-restricted</default-behaviour></originating-identity-presentation-restriction><communication-diversion active="true"><NoReplyTimer>30</NoReplyTimer><cp:ruleset/></communication-diversion><incoming-communication-barring active="true"><cp:ruleset><cp:rule id="rule0"><cp:conditions/><cp:actions><allow>true</allow></cp:actions></cp:rule></cp:ruleset></incoming-communication-barring><outgoing-communication-barring active="true"><cp:ruleset><cp:rule id="rule0"><cp:conditions/><cp:actions><allow>true</allow></cp:actions></cp:rule></cp:ruleset></outgoing-communication-barring></simservs>"""
