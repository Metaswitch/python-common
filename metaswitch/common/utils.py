# @file utils.py
#
# Project Clearwater - IMS in the Cloud
# Copyright (C) 2013  Metaswitch Networks Ltd
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation, either version 3 of the License, or (at your
# option) any later version, along with the "Special Exception" for use of
# the program along with SSL, set forth below. This program is distributed
# in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details. You should have received a copy of the GNU General Public
# License along with this program.  If not, see
# <http://www.gnu.org/licenses/>.
#
# The author can be reached by email at clearwater@metaswitch.com or by
# post at Metaswitch Networks Ltd, 100 Church St, Enfield EN2 6BQ, UK
#
# Special Exception
# Metaswitch Networks Ltd  grants you permission to copy, modify,
# propagate, and distribute a work formed by combining OpenSSL with The
# Software, or a work derivative of such a combination, even if such
# copying, modification, propagation, or distribution would otherwise
# violate the terms of the GPL. You must comply with the GPL in all
# respects for all of the code used other than OpenSSL.
# "OpenSSL" means OpenSSL toolkit software distributed by the OpenSSL
# Project and licensed under the OpenSSL Licenses, or a work based on such
# software and licensed under the OpenSSL Licenses.
# "OpenSSL Licenses" means the OpenSSL License and Original SSLeay License
# under which the OpenSSL Project distributes the OpenSSL toolkit software,
# as those licenses appear in the file LICENSE-OPENSSL.

import os
import sys
import re
import logging
import math
import binascii
import base64
from tornado import ioloop
import threading
import traceback
import phonenumbers
import hashlib
import bcrypt
from urllib import quote
from Crypto.Cipher import Blowfish

_log = logging.getLogger("metaswitch.utils")

# The length of a UUID in bytes
UUID_LEN = 20
# The length of an audible ID in decimal digits
UUID_LEN_AUDIBLE = 4

def create_secure_random_id(length=UUID_LEN):
    """Securely create a new secret ID, encoded as a hex string.  The ID is
       created at random but is very likely to be unique."""
    random_bytes = os.urandom(length)
    return binascii.hexlify(random_bytes)

# Alphabet used for generating human-readable IDs.  We want this to have
# several properties:
#  - no characters that are easily mistaken for each other (1, l, i, 0, o)
#  - lower case because it's easier to read
#  - no u, to avoid unintended profanity
#  - URL-safe
_HUMAN_SAFE_ALPHABET = "abcdefghjkmnpqrstvwxyz3456789"
_HUMAN_SAFE_MIXED_CASE_ALPHABET = "abcdefghjkmnpqrstvwxyz3456789ABCDEFGHKMNPQRSTVWXYZ"

# Alphabet for URL-safe IDs, we want all the characters to be URL-safe.  We
# don't expect humans to transcribe it manually.
_URL_SAFE_ALPHABET = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

# Alphabet for playing in calls
_AUDIBLE_ALPHABET = "0123456789"

# Map from commonly substituted letter back to letter of the safe alphabet.
_HUMAN_SUBSTITUTIONS = {'u': 'v', 'i': 'j', '2': 'z'}

# Regular expression splitting apart a SIP(S) URI.
_SIP_URI_REGEXP = r'^sips?:(?P<number>[0-9+]+)(?::(?P<password>))?@(?P<domain>[^;]+).*$'

def _create_secure_id_length_function(alphabet):
    """
    Creates an ID generator function that uses the given alphabet.  The
    returned function accepts a single argument which is the length of
    the id to generate.
    """
    # To avoid bias we need to restrict the random byte values that we use to
    # a subset whose size is divisible by the size of the alphabet.
    alphabet_length = len(alphabet)
    greatest_multiple = alphabet_length * int(256 // alphabet_length)

    def create_id(required_length):
        id = ""
        length = 0
        random_iter = generate_secure_random_bytes(required_length * 2)
        while length < required_length:
            # The id isn't long enough yet, add some more random stuff on the
            # end.  First, pick a random byte and truncate it to the greatest
            # multiple of the alphabet length that fits in a byte.
            random_byte = next(random_iter)
            if random_byte < greatest_multiple:
                # The truncated byte is within our truncated space, use it.  If
                # it wasn't, we'd just loop again and have another chance at
                # picking a value within our alphabet.  Schemes without a retry
                # in that case have to be very clever to avoid introducing bias.
                idx = random_byte % alphabet_length
                length += 1
                id += alphabet[idx]
        return id

    return create_id

def _create_secure_id_bits_function(alphabet):
    """
    Creates an ID generator function that uses the given alphabet.  The
    returned function will accept a single argument, which is the strength
    (in bits) of the id to generate.
    """
    bits_per_char = math.log(len(alphabet), 2)
    id_length_function = _create_secure_id_length_function(alphabet)

    def create_id(strength_in_bits):
        required_length = math.ceil(strength_in_bits / bits_per_char)
        return id_length_function(required_length)

    return create_id

create_secure_human_readable_id = _create_secure_id_bits_function(_HUMAN_SAFE_ALPHABET)
"""Securely creates an ID using characters that are appropriate for human
copying.

strength_in_bits: the number of bits of entropy that must be incorporated
into the key.  The function tries to minimize the length of the key while
still providing that much entropy.
"""

create_secure_mixed_case_human_readable_id = _create_secure_id_bits_function(_HUMAN_SAFE_MIXED_CASE_ALPHABET)
"""Securely creates an ID using characters that are appropriate for human
copying.

strength_in_bits: the number of bits of entropy that must be incorporated
into the key.  The function tries to minimize the length of the key while
still providing that much entropy.
"""

create_secure_url_safe_id = _create_secure_id_bits_function(_URL_SAFE_ALPHABET)
"""Securely creates an ID using characters that are appropriate for use in a URL
without percent-encoding.

strength_in_bits: the number of bits of entropy that must be incorporated
"""

_create_audible_random_id_by_length = _create_secure_id_length_function(_AUDIBLE_ALPHABET)
create_audible_random_id = lambda: _create_audible_random_id_by_length(UUID_LEN_AUDIBLE)
"""Securely creates an ID using characters that are suitable to be read out in
a call.
"""
create_short_code = _create_audible_random_id_by_length
"""Create a short code for activation"""

def correct_human_readable_id(id):
    """
    Does some basic error correction on the human-readable ID, replacing
    commonly confused letters etc.
    """
    # Our IDs are lower case
    id = id.lower()
    for char, subs in _HUMAN_SUBSTITUTIONS.iteritems():
        id = id.replace(char, subs)
    return id

URANDOM_BUFFER_SIZE = 128
def generate_secure_random_bytes(buffer_size=URANDOM_BUFFER_SIZE):
    """
    Generator that yields one securely-random byte for each next()
    invocation.  Buffers the underlying random output in chunks of buffer_size.

    the iterator should not be used by multiple threads concurrently.
    """
    while True:
        bytes = os.urandom(URANDOM_BUFFER_SIZE)
        for x in bytes:
            yield ord(x)

_main_thread = None
_thread_violation = False

def assert_main_thread():
    global _main_thread
    global _thread_violation
    my_thread = threading.current_thread().ident
    if _main_thread is not None:
        if my_thread != _main_thread:
            try:
                _thread_violation = True
                raise AssertionError("This function should only be called from the main thread")
            except:
                _log.exception("This function should only be called form the main thread")
                raise
    else:
        # We don't know what the main thread is yet.  Queue up an action on
        # the main thread to save it off and then check this thread was
        # correct.
        my_stack = traceback.format_stack()
        def _set_main_thread():
            global _main_thread
            global _thread_violation
            _main_thread = threading.current_thread().ident
            if my_thread != _main_thread:
                _thread_violation = True
                raise AssertionError("This function should only be called "
                                     "from the main thread.  Original stack:\n" +
                                     "".join(my_stack))
        ioloop.IOLoop.instance().add_callback(_set_main_thread)

def sip_uri_to_phone_number(sip_uri):
    match = re.match(_SIP_URI_REGEXP, sip_uri)
    if match:
        return match.group("number")
    else:
        return "Unknown"

def sip_uri_to_domain(sip_uri):
    match = re.match(_SIP_URI_REGEXP, sip_uri)
    if match:
        return match.group("domain")
    else:
        return "Unknown"

def format_phone_number(number):
    try:
        # TODO support non-US
        numobj = phonenumbers.parse(number, "US")
        number = phonenumbers.format_number(numobj,
                                            phonenumbers.PhoneNumberFormat.NATIONAL)
    except Exception:
        return number
    return number


def sip_lists_to_phone_list(list_of_sip_numbers):
    return [sip_uri_to_phone_number(x)
        for x in list_of_sip_numbers]


def delete_if_exists(fn):
    try:
        os.unlink(fn)
    except OSError:
        pass

def md5(s):
    digest = hashlib.md5()
    digest.update(s)
    return digest.hexdigest()

BASE64_ALT_CHARS = '-_'

def encrypt_password(password, key):
    """
    Encrypts a password with the given key, the result contains enough metadata
    for decrypt_password to determine the type of encryption.  The result is
    encoded to be ASCII-safe.

    To avoid ambiguity when decoding, password should be a unicode string.
    """
    binary = password.encode("utf-8")
    encrypted = encrypt_with_blowfish(binary, key)
    encoded = base64.b64encode(encrypted, BASE64_ALT_CHARS)
    encoded = encoded.rstrip("=")
    return "b%s" % encoded

def decrypt_password(encoded_password, key):
    """
    Decrypts a password encrypted via encrypt_password.  Returns the decrypted
    password.
    """
    encoded_password = encoded_password.encode("ASCII")
    type = encoded_password[0]
    if type != "b":
        raise Exception("Encoded password wasn't in supported format")
    b64_encoded = encoded_password[1:]
    num_pad_chars = (-len(b64_encoded)) % 4
    b64_encoded += "=" * num_pad_chars
    ciphertext = base64.b64decode(b64_encoded, BASE64_ALT_CHARS)
    return decrypt_with_blowfish(ciphertext, key).decode("utf-8")

def _pad(input, block_size):
    """
    Pads the input binary string to a multiple of block_size in a way that is
    100% reversible by _un_pad.
    """
    num_zeros = (-1 - len(input)) % block_size
    output = input + "\x80" + ("\x00" * num_zeros)
    assert len(output) % block_size == 0
    return output

def _un_pad(input):
    """
    Removes the padding added by _pad.
    """
    idx = input.rfind('\x80')
    assert idx >= 0
    return input[:idx]

def encrypt_with_blowfish(plaintext, key):
    """
    Encrypts the given plaintext, which should already be encoded as a binary
    str (not a unicode) with the given key.  Performs the required padding
    automatically.
    """
    assert isinstance(plaintext, str), "Plaintext should be a binary string"
    iv = os.urandom(8)
    padded = _pad(plaintext, 8)
    bf = Blowfish.new(key, Blowfish.MODE_CBC, IV=iv)
    ciphertext = bf.encrypt(padded)
    return iv + ciphertext

def decrypt_with_blowfish(ciphertext, key):
    """
    Decrypts a string encrypted with "encrypt_with_blowfish".  Undoes any
    padding.
    """
    iv = ciphertext[:8]
    ciphertext = ciphertext[8:]
    bf = Blowfish.new(key, Blowfish.MODE_CBC, IV=iv)
    plaintext = bf.decrypt(ciphertext)
    plaintext = _un_pad(plaintext)
    return plaintext

def hash_password(password):
    """Hashes the given password using bcrypt."""
    binary = password.encode("utf-8")
    hashed = bcrypt.hashpw(binary, bcrypt.gensalt(10)) #@UndefinedVariable
    return hashed

def is_password_correct(password, hashed):
    """returns True if the password matches the given bcrypt hash."""
    binary = password.encode("utf-8")
    return bcrypt.hashpw(binary, hashed) == hashed #@UndefinedVariable

def encode_query_string(params):
    """
    Encode a query string, suitable for decoding by JavaScript's
    decodeURIComponent.  I.e. '+' is encoded as %2B, ' ' as %20, etc.

    Note: urllib's urlencode function quotes ' ' as '+', which doesn't get
    decoded correctly by decodeURIComponent.
    """
    kvps = []
    for k, v in sorted(params.items()):
        k = k.encode("utf-8")
        if isinstance(v, basestring):
            v = v.encode("utf-8")
        else:
            v = str(v)
        kvps .append("%s=%s" % (quote(k.encode("utf-8")), quote(v.encode("utf-8"))))
    return "&".join(kvps)

def append_url_params(url, **params):
    hash = None
    if "#" in url:
        url, _, hash = url.partition("#")
    if url == "": url = "?"
    sep = "" if url[-1] in ("?", "&") else ("&" if "?" in url else "?")
    url = url + sep + encode_query_string(params)
    if hash:
        url = url + "#" + hash
    return url

def generate_sip_password():
    return create_secure_mixed_case_human_readable_id(48)

def sip_public_id_to_private(public_id):
    """returns the default private ID for a given public ID (by stripping any sip: prefix)"""
    return re.sub('^sip:', '', public_id)

def daemonize(filename):
    """
    Place application in background and exit.
    Based on http://code.activestate.com/recipes/66012-fork-a-daemon-process-on-unix/
    Preserves cwd - if you don't want this, be sure to do os.chdir().

    Appends any stdout/stderr to the named file.
    """

    outfile = file(filename, 'a+')
    dev_null = file('/dev/null', 'r')

    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0)
    except OSError, e:
        print >>sys.stderr, "Unable to daemonize process: %d (%s)" % (e.errno, e.strerror)
        sys.exit(1)

    os.setsid()
    os.umask(0)

    os.dup2(outfile.fileno(), sys.stdout.fileno())
    os.dup2(outfile.fileno(), sys.stderr.fileno())
    os.dup2(dev_null.fileno(), sys.stdin.fileno())
    outfile.close()
    dev_null.close()

    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0)
    except OSError, e:
        sys.exit(1)
