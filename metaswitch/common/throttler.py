# @file throttler.py
#
# Copyright (C) Metaswitch Networks 2017
# If license terms are provided to you in a COPYING file in the root directory
# of the source code repository by which you are accessing this code, then
# the license outlined in that COPYING file applies to your use.
# Otherwise no rights are granted except for those provided to you by
# Metaswitch Networks in a separate written agreement.


import logging
import threading
import time

_log = logging.getLogger("metaswitch.utils")

class Throttler:
    """Simple leaky-bucket throttler."""

    def __init__(self, rate_per_second, burst_count):
        """Constructor.

        Arguments:
        rate_per_second -- the maximum sustained event rate to allow
        per second.
        burst_count -- the maximum number of events to allow at once.
        """
        self._rate_per_second = rate_per_second
        self._burst_count = burst_count
        self._bucket = self._burst_count
        self._last_update = time.time()
        self._lock = threading.Lock()

    def is_allowed(self):
        """Attempt an event and determine if it is allowed.

        Returns True if it is allowed, and False if it is throttled.
        """
        with self._lock:
            now = time.time()
            delta = (now - self._last_update) * self._rate_per_second
            bucket = self._bucket + delta
            self._bucket = min(self._burst_count, bucket)
            self._last_update = time.time()
            # _log.debug("Bucket %f, last update %f", self._bucket, self._last_update)
            if self._bucket >= 1:
                self._bucket -= 1
                return True
            else:
                return False
            
    @property
    def interval_sec(self):
        """The typical sustained interval between events,
        as an integer number of seconds.

        Never less than 1."""
        return max(1, int(1 / self._rate_per_second))
