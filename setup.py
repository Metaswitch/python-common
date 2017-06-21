# @file setup.py
#
# Copyright (C) Metaswitch Networks 2016
# If license terms are provided to you in a COPYING file in the root directory
# of the source code repository by which you are accessing this code, then
# the license outlined in that COPYING file applies to your use.
# Otherwise no rights are granted except for those provided to you by
# Metaswitch Networks in a separate written agreement.

import logging
import sys

from setuptools import setup, Extension
from logging import StreamHandler

_log = logging.getLogger("common")
_log.setLevel(logging.DEBUG)
_handler = StreamHandler(sys.stderr)
_handler.setLevel(logging.DEBUG)
_log.addHandler(_handler)

setup(
    name='metaswitchcommon',
    version='0.1',
    packages=['metaswitch', 'metaswitch.common'],
    package_dir={'':'.'},
    test_suite='metaswitch.common.test',
    setup_requires=["cffi"],
    ext_package="metaswitch.common",
    cffi_modules=["cffi_build.py:ffi"],
    install_requires=[
        "cffi==1.10.0",
        "monotonic==0.6",
        "py-bcrypt==0.4",
        "pycparser==2.17",
        "pycrypto==2.6.1",
        "pyzmq==16.0.2"],
    tests_require=[
        "funcsigs==1.0.2",
        "Mock==2.0.0",
        "pbr==1.6",
        "phonenumbers==7.1.1",
        "six==1.10.0"]
    )
