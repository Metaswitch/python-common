import logging
import collections
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
        columns.append("INDEX")
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
    def __repr__(self):
        return self.details['SNMP NAME']

    def __init__(self, oid, mib_file, columns):
        '''
        Input
        oid:       The specific OID for the statistic
        mib_file:  The location of the MIB file defining the statistic
        columns:   The properties of the statistic that we want to parse
        '''
        logger.info('Generating an element of class Statistic for OID: %s',
                    oid)
        # Cache parent and table values.
        self._table = None
        self._parent = None

        self.mib_file = mib_file
        self.columns = columns
        self.details = {}
        self.oid = oid

        tokenized_details = _get_tokenized_mib_details(mib_file, oid)

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
            logger.warning('could not find a %s for OID %s', name, self.oid)
            return False

    def parent(self):
        """Get the parent statistic.

        Raises `LookupError` if no parent can be found."""
        if not self._parent:
            oid = self.details['OID']
            logger.debug("Getting parent of OID %s", oid)
            parent_oid = oid.rsplit('.', 1)[0]
            if oid == parent_oid:
                raise LookupError("At root of OID tree.")
            self._parent = Statistic(parent_oid, self.mib_file, self.columns)
        return self._parent

    def ancestors(self):
        """Get an iterator of ancestor nodes for this Statistic."""
        ancestor = self
        while True:
            try:
                ancestor = ancestor.parent()
                yield ancestor
            except LookupError:
                break

    def table(self):
        """Get a Statistic for the table this Statistic belongs to.

        Raises `LookupError` if no table can be found.
        """
        # Implementation is to look back through the parents of this node
        # until we find one with "Table" in it's name.
        def table_test(stat):
            return True if  "Table" in stat.get_info("SNMP NAME") else False

        if not self._table:
            for ancestor in self.ancestors():
                if table_test(ancestor):
                    logger.debug('Found table for Statistic %s: %s',
                                 self.get_info("SNMP NAME"),
                                 ancestor.get_info("SNMP NAME"))
                    break
            else:
                raise LookupError("OID not in table.")
            self._table = ancestor

        return self._table


    def is_index_field (self):
        """Determine if this is an index field or not by stepping back through
        the ancestors inside the table.

        Raises `LookupError` if the statistic is not in a table."""

        field_name = self.get_info("SNMP NAME")
        self.table()

        for ancestor in self.ancestors():
            ancestor_index_string = ancestor.get_info("INDEX")
            if ancestor_index_string:
                # String should be of form { comma separated indices } or
                # blank if no indices. Check that there's an acutal string to
                # parse then split it into separate elements and look for a
                # match with the field name.
                ancestor_index_string = ancestor_index_string[2:-2]

                if len(ancestor_index_string) > 0:
                    ancestor_index_fields = \
                          [x.strip() for x in ancestor_index_string.split(',')]
                    if field_name in ancestor_index_fields:
                        return True
        return False


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


class memoize(collections.defaultdict):
    """Memoize the return values from a function."""
    def __call__(self, *args):
        return self[args]
    def __missing__(self, args):
        value = self.default_factory(*args)
        self[args] = value
        return value


@memoize
def _get_tokenized_mib_details(mib_file, oid):
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
    print get_details_cmd

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
