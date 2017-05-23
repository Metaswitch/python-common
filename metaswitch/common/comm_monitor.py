# @file comm_monitor.py
#
# Copyright (C) Metaswitch Networks 2017
# If license terms are provided to you in a COPYING file in the root directory
# of the source code repository by which you are accessing this code, then
# the license outlined in that COPYING file applies to your use.
# Otherwise no rights are granted except for those provided to you by
# Metaswitch Networks in a separate written agreement.

import logging
from threading import Lock
from alarms import alarm_manager
from monotonic import monotonic

_log = logging.getLogger(__name__)

class CommunicationMonitor(object):
    def __init__(self, process, alarm_handle, raise_pd, clear_pd):
        self._alarm = alarm_manager.get_alarm(process, alarm_handle)
        self._alarm_handle = alarm_handle
        self._raise_pd = raise_pd
        self._clear_pd = clear_pd
        self.succeeded = 0
        self.failed = 0
        self.alarmed = False
        self.mutex = Lock()
        self._next_check = 0

    def set_alarm(self):
        self.alarmed = True
        _log.warning("Raising alarm %s.", self._alarm_handle)
        self._raise_pd.log()
        self._alarm.set()

    def clear_alarm(self):
        self.alarmed = False
        _log.warning("Clearing alarm %s.", self._alarm_handle)
        self._clear_pd.log()
        self._alarm.clear()

    def update_alarm_state(self):
        now = monotonic()
        with self.mutex:
            _log.debug("Deciding whether to change alarm state - alarmed is {}, now is {}, next check time is {}, succeeded count is {}, failed count is {}"
                       .format(self.alarmed, now, self._next_check, self.succeeded, self.failed))
            if (now > self._next_check):
                _log.debug("Checking alarm state")
                if not self.alarmed:
                    if self.succeeded == 0 and self.failed > 0:
                        self.set_alarm()
                    self._next_check = now + 30
                else:
                    if self.succeeded > 0:
                        self.clear_alarm()
                    self._next_check = now + 15
                self.succeeded = self.failed = 0

    def inform_success(self):
        self.succeeded += 1
        self.update_alarm_state()

    def inform_failure(self):
        self.failed += 1
        self.update_alarm_state()
