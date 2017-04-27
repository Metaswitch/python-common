import logging
import subprocess

logger = logging.getLogger(__name__)


class MibFile(object):
    """Parser for MIB files.

    `path` is the path to the MIB file on disk.
    """
    def __init__(self, path):
        self.path = path
        self._oids = None

    @property
    def oids(self):
        '''Generates a list of OID's from the MIB file

        Input
        location:    location of the current mib file being accessed
        '''
        if self._oids is None:
            logger.info('Generating_OID_list from file: %s', self.path)
            with open('/dev/null', 'w') as the_bin:
                command = ['snmptranslate', '-m', self.path, '-To']
                oid_string = subprocess.check_output(command, stderr=the_bin)
                oid_list = oid_string.split()
            logger.debug('Generated OID list %s', oid_list)
            self._oids = oid_list
        return self._oids

    def get_all_stats(self, columns):
        """Parse information for all the OIDs in the file.

        `input_file` should be the absolute path to a MIB file.
        `columns` should be a list of the properties of the statistic that we
        want to parse.
        """
        stats = {oid: Statistic(oid, self.path, columns) for
                 oid in self.oids}
        return stats

    def get_oids_at_depth(self, depth):
        ''' Generates a list of statistics of a given length in the mib.

            Input
            oid_list:           A list of the oid's to be checked through,
                                usually from the MIB
            depth:              the depth or length that the OID should be

            Return:             A list of all of the valid OID's
        '''
        logger.info('getting OID\'s at depth %s', depth)
        return filter(lambda oid: len(oid.split('.')) == depth, self.oids)


class Statistic(object):
    ''' The class structure for each OID and its relevant information
    '''

    def __init__(self, oid, mib_file, columns):
        '''
        Input
        oid:       The specific OID for the statistic
        mib_file:  The location of the MIB file defining the statistic
        columns:   The properties of the statistic that we want to parse
        '''
        logger.info('Generating an element of class Statistic for OID: %s',
                    oid)

        self.mib_file = mib_file
        self.columns = columns
        self.details = {}

        tokenized_details = self._get_tokenized_mib_details(mib_file, oid)

        for item in columns:
            try:
                item_index = tokenized_details.index(item)
                self.details[item] = tokenized_details[item_index+1]
                if self.details[item][0] == '\"':
                    self.details[item] = self.details[item].strip('\"')
            except:
                self.details[item] = "N/A"

        with open('/dev/null', 'w') as the_bin:
            command = ['snmptranslate', '-m', mib_file, oid]
            name = subprocess.check_output(command,
                                           stderr=the_bin)

        # name is in the form  MIB_FILE_NAME::snmp name
        self.details['SOURCE FILE'] = name.split('::')[0].strip()
        self.details['SNMP NAME'] = name.split('::')[1].strip()
        self.details['OID'] = oid.strip()

        logger.debug('generated object of class statistic with OID %s and'
                     ' details %s' % (oid, self.details))

    def get_info(self, name):
        if name in self.details:
            return self.details[name]
        else:
            return False
            logger.warning('could not find a %s for OID %s', name, self.oid)

    def parent(self):
        """Return the parent statistic."""
        parent_oid = self.details['OID'].rsplit('.', 1)[0]
        return Statistic(parent_oid, self.mib_file, self.columns)

    def _get_tokenized_mib_details(self, mib_file, oid):
        ''' Gets the details for a statistics from a MIB file.   Splits them by
            whitespace and then regroups anything that is inside {} or "" in
            keeping with ASN1 syntax.

            Input
            mib_file:           The MIB file defining the statistic
            oid:                The OID of the statistic we are interested in
            Return:             A list of tokens, where a token is either a
                                single word or all words enclosed within {} or
                                "".
        '''
        get_details_cmd = ['snmptranslate', '-m', mib_file, '-Td', oid]
        with open('/dev/null', 'w') as the_bin:
            detail_string = subprocess.check_output(get_details_cmd,
                                                    stderr=the_bin)

        in_quotes = False
        in_braces = False
        output = []
        split_string = detail_string.split()

        for word in split_string:
            if in_quotes or in_braces:
                output[-1] = ' '.join([output[-1], word])
            else:
                output.append(word)

            for character in word:
                if character == '\"':
                    in_quotes = not in_quotes
                elif character == '{' or character == '}':
                    in_braces = not in_braces

        return output

    def get_data(self, columns):
        ''' Gets the data from a stat. If the stat is an intermediate node or
            blacklisted, returns None.

            Input
            stat:               Statistic object to be processed
        '''
        data = None

        # If MAX-ACCESS is N/A, this is an intermediate node of no interest, and
        # we skip it.
        if not stat.get_info('MAX-ACCESS') == "N/A":
            stat_name = stat.get_info('SNMP NAME')
            if should_output_stat(stat_name):
                data = [stat.get_info(detail) for detail in columns]

        return data