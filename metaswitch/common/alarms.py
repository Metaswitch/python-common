# @file alarms.py
#
# Project Clearwater - IMS in the Cloud
# Copyright (C) 2015 Metaswitch Networks Ltd
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


# This module provides a method for transporting alarm requests to a net-
# snmp alarm sub-agent for further handling. If the agent is unavailable,
# the request will timeout after 2 seconds and be dropped.


import logging
import atexit
from monotonic import monotonic
import threading
import imp

_log = logging.getLogger(__name__)

# Imported sendrequest method set up in issue_alarm.
_sendrequest = None

CLEARED = 1
INDETERMINATE = 2
CRITICAL = 3
MAJOR = 4
MINOR = 5
WARNING = 6


class _AlarmManager(threading.Thread):
    """
    Singleton iterface to alarm code.

    Use the instance alarm_manager as the single entry point into alarm
    handling code.

    Keeps a record of all alarms and makes sure they are re-raised
    periodically.
    """
    # Interval in seconds.
    RE_SYNC_INTERVAL = 30

    def __init__(self):
        self._alarm_registry = {}
        self._condition = threading.Condition()
        self._registry_lock = threading.Lock()
        self._next_resync_time = monotonic() + self.RE_SYNC_INTERVAL
        self._should_terminate = False
        self._running = False

    def get_alarm(self, issuer, alarm_handle):
        with self._alarm_lock:
            alarm = self._alarm_registry.get((issuer, alarm_handle), None)

            if not alarm:
                index = alarm_handle[0]
                severities = alarm_handle[1:]
                severities.remove(CLEARED)

                if len(severities) == 1:
                    alarm = Alarm(issuer, index, severities[0])
                elif len(severities) > 1:
                    alarm = MultiSeverityAlarm(issuer, index, severities)
                else:
                    raise ValueError('alarm_handle must contain a severity.')

                self._alarm_registry[(issuer, alarm_handle)] = alarm
                should_start = (not self._running) and (not self._should_terminate)

        if should_start:
            self.start()
            atexit.register(self.terminate)

        return alarm

    def run(self):
        with self._condition:
            while True:
                sleep_time = self._get_sleep_time()
                self._condition.wait(sleep_time)
                if self._should_terminate:
                    break;
                self._re_sync_alarms()

    def terminate(self):
        with self._condition:
            self._should_terminate = True
            self._condition.notify()

    def _re_sync_alarms(self):
        current_alarms = self._alarm_registry.values()
        for alarm in current_alarms:
            alarm.re_sync()

    def _get_sleep_time(self):
        self._next_resync_time += 30
        current_time = monotonic()
        sleep_time = self._next_resync_time - current_time

        if sleep_time <= 0:
            _log.error('Missed alarm re-sync time by %ds', -sleep_time)
            skips = ((sleep_time / self.RE_SYNC_INTERVAL) + 1)
            self._next_resync_time += skips * self.RE_SYNC_INTERVAL
            sleep_time = next_resync_time - current_time

        return sleep_time

alarm_manager = _AlarmManager()


class BaseAlarm(object):
    def __init__(self, issuer, index):
        _alarm_manager.register(self)
        self._clear_state = AlarmState(issuer, index, CLEARED)
        self._last_state_raised = self._clear_state

    def clear(self):
        self._last_state_raised = self._clear_state
        self.re_sync()

    def re_sync(self):
        self._last_state_raised.notify()


class Alarm(object):
    def __init__(self, issuer, index, severity):
        super(Alarm, self).__init__(issuer, index)
        self._alarm_state = AlarmState(issuer, index, severity)

    def set(self):
        self._last_state_raised = self._alarm_state
        self.re_sync()


class MultiSeverityAlarm(object):
    def __init__(self, issuer, index, severities):
        super(MultiSeverityAlarm, self).__init__(issuer, index)
        self._severities = {severity: AlarmState(issuer, index, severity) for
                            severity in severities}

    def set(self, severity):
        try:
            self._last_state_raised = self._severities[severity]
        except KeyError:
            _log.error('Attempted to raise incorrect alarm state %s',
                       severity)
            raise

        self.re_sync()

    def clear(self):
        self._last_state_raised = self._clear_state
        self.re_sync()


class AlarmState(object):
    def __init__(self, issuer, index, severity):
        self.issuer = issuer
        self.index = index
        self.severity = severity

    def notify(self):
        identifier = '{}.{}'.format(self.index, self.severity)
        _issue_alarm(issuer, identifier)


def _issue_alarm(process, identifier):
    # Clearwater nodes all have clearwater-infrastructure installed.
    # It includes a command-line script that can be used to issue an alarm.
    # We import the function used by the script and re-use it.
    #
    # See https://github.com/Metaswitch/clearwater-infrastructure/blob/master/clearwater-infrastructure/usr/share/clearwater/bin/alarms.py
    # for the target module.
    global _sendrequest
    if _sendrequest is None:
        try:
            file, pathname, description = imp.find_module("alarms", ["/usr/share/clearwater/bin"])
            mod = imp.load_module("alarms", file, pathname, description)
            _sendrequest = mod.sendrequest
            _log.info("Imported /usr/share/clearwater/bin/alarms.py")
        except ImportError:
            _log.error("Could not import /usr/share/clearwater/bin/alarms.py, alarms will not be sent")

    if _sendrequest:
        _sendrequest(["issue-alarm", process, identifier])
