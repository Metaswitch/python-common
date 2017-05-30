# @file alarms.py
#
# Copyright (C) Metaswitch Networks 2016
# If license terms are provided to you in a COPYING file in the root directory
# of the source code repository by which you are accessing this code, then
# the license outlined in that COPYING file applies to your use.
# Otherwise no rights are granted except for those provided to you by
# Metaswitch Networks in a separate written agreement.

"""
Interface for raising and clearing alarms in Python code.

This module provides the interface for raising and clearing alarms in our
python code.  Alarms should be raised using the classes in this module to
ensure that they have the correct retry and re-synchronization logic applied.

Users should use the alarm_manager to get an instance of the alarm they
wish to raise, then use its set and clear methods to update alarm state.

The module also exposes constants expressing alarm severities.
"""
# Note, the class structure is based on the alarm objects in cpp-common.
# The two implementations should be kept in step where possible.
import logging
import atexit
from monotonic import monotonic
import threading
import imp
from alarm_severities import (CLEARED,
                              INDETERMINATE,
                              CRITICAL,
                              MAJOR,
                              MINOR,
                              WARNING)

_log = logging.getLogger(__name__)


def unused_variable(*names):
    """Mark variables as unused to avoid flake8 warnings."""

unused_variable(CLEARED,
                INDETERMINATE,
                CRITICAL,
                MAJOR,
                MINOR,
                INDETERMINATE,
                WARNING)

# Imported sendrequest method set up in issue_alarm.
_sendrequest = None

# How often to re-sync alarms in seconds.
RE_SYNC_INTERVAL = 30


class _AlarmManager(threading.Thread):
    """
    Singleton interface to alarm code.

    Use the instance alarm_manager as the single entry point into alarm
    handling code.

    Keeps a record of all alarms and makes sure they are re-raised
    every RE_SYNC_INTERVAL seconds.
    """

    def __init__(self):
        super(_AlarmManager, self).__init__()

        # Make the thread daemon so that the process can exit while the
        # alarm loop is still running. This means that users don't need
        # to terminate the alarm_manager explicitly.
        self.daemon = True
        self._alarm_registry = {}
        self._condition = threading.Condition()
        self._registry_lock = threading.Lock()

        # The re-sync code with nudge this forward by RE_SYNC_INTERVAL so no
        # need to increment on initialization.
        self._next_resync_time = monotonic()
        self._should_terminate = False
        self._running = False

    def get_alarm(self, issuer, alarm_handle):
        """Get a control for an alarm.

        If the alarm described by alarm_handle has a single non-cleared severity,
        return an Alarm representing the object. If the alarm has multiple
        severities, return a MultiSeverityAlarm.

        alarm_handle should be a constant defined in alarm_constants.
        alarm_constants is generated for a project by running alarm_writer.py
        over the JSON alarm definition file. For all of our projects, this is
        done as part of the build process.

        Alarm handles should be of the following form:
        `(<index_number>, <severity1>, <severity2>, ...)`
        """

        # We only want to start if we're not already running and we have an
        # alarm, so we define this flag to track those criteria.
        should_start = False

        # Prevent two threads from creating the same alarm object.
        with self._registry_lock:
            alarm = self._alarm_registry.get((issuer, alarm_handle), None)

            if not alarm:
                # See format description in docstring.
                index = alarm_handle[0]
                severities = list(alarm_handle[1:])
                severities.remove(CLEARED)

                if len(severities) == 1:
                    alarm = Alarm(issuer, index, severities[0])
                elif len(severities) > 1:
                    alarm = MultiSeverityAlarm(issuer, index, severities)
                else:
                    raise ValueError('alarm_handle must contain a severity.')

                self._alarm_registry[(issuer, alarm_handle)] = alarm
                should_start = ((not self._running) and
                                (not self._should_terminate))

                # Make sure that no other thread tries to start the thread
                # as threads must only be started once.
                self._running = True

        # It would be wasteful to start the alarm re-sync thread with
        # no alarms present.
        if should_start:
            self.start()

            # Note, this creates a reference to the alarm_manager, which
            # means that it will not be cleaned up until exit. This is
            # fine for a singleton which is expected to run until exit.
            atexit.register(self.terminate)

        return alarm

    def run(self):
        """Run loop to keep alarms in sync."""
        with self._condition:
            while True:
                sleep_time = self._update_resync_time()

                # Cope with the fact that we may be woken up early and
                # have to sleep again.
                while (sleep_time > 0):
                    self.loop_done_hook()
                    self._condition.wait(sleep_time)
                    if self._should_terminate:
                        break
                    sleep_time = self._next_resync_time - monotonic() # pragma: no cover

                if self._should_terminate:
                    break
                self._re_sync_alarms() # pragma: no cover

            # Tell the terminating thread that it's safe to
            # exit.
            _log.info('Alarm manager shut down.')
            self.loop_done_hook()
            self._condition.notify()

    def terminate(self):
        """Stop the run loop cleanly."""
        _log.info('Shutting down alarm manager.')
        with self._condition:
            self._should_terminate = True
            self._condition.notify()

            # Wait for the run loop to finish. It should finish
            # after 2s as this is when an attempt to send a message
            # times out. Give it a couple of extra seconds, then exit.
            _log.info('Waiting for alarm manager to quiesce.')
            self._condition.wait(4)

    def loop_done_hook(self):
        """Hook for subclasses to override to run code each runloop cycle.

        This allows test subclasses to wait for a single loop of the main
        runloop, then test the result."""
        pass

    def _re_sync_alarms(self): # pragma: no cover
        """Re-sync each alarm in the registry."""
        current_alarms = self._alarm_registry.values()

        # Each alarm sync may take up to 2s on failure. This could
        # easily add up to more than the RE_SYNC_INTERVAL. In this case,
        # a log will be written by _get_sleep_time. The expected cause
        # of long request times is that alarm agent is not available;
        # in this case it makes little difference which alarms we are
        # failing to re-sync, so there is no need for timeout logic.
        for alarm in current_alarms:
            if self._should_terminate: # pragma: no cover
                # There is no way of ensuring that we hit this condition.
                break
            alarm.re_sync()

    def _update_resync_time(self):
        """Calculate how long to sleep before the next re-sync."""
        self._next_resync_time += 30
        current_time = monotonic()
        sleep_time = self._next_resync_time - current_time

        if sleep_time <= 0: # pragma: no cover
            missed_by = -sleep_time
            _log.error('Missed alarm re-sync time by %ds', missed_by)
            skips = ((missed_by / RE_SYNC_INTERVAL) + 1)
            self._next_resync_time += (skips * RE_SYNC_INTERVAL)
            sleep_time = self._next_resync_time - current_time

        return sleep_time


alarm_manager = _AlarmManager()


class BaseAlarm(object):
    def __init__(self, issuer, index):
        self._clear_state = AlarmState(issuer, index, CLEARED)
        self._last_state_raised = None

    def clear(self):
        """Send the alarm's cleared state to the alarm agent."""
        self._last_state_raised = self._clear_state
        self.re_sync()

    def re_sync(self):
        """Send or re-send the alarm's state to the alarm agent."""
        if self._last_state_raised is not None:
            self._last_state_raised.issue()


class Alarm(BaseAlarm):
    """Alarm with only a single non-cleared severity.

    The parameter severity should be passed a severity constant from this
    module"""
    def __init__(self, issuer, index, severity):
        super(Alarm, self).__init__(issuer, index)
        self._alarm_state = AlarmState(issuer, index, severity)

    def set(self):
        """Send the alarm's raised state to the alarm agent."""
        self._last_state_raised = self._alarm_state
        self.re_sync()


class MultiSeverityAlarm(BaseAlarm):
    """Alarm with multiple possible non-cleared severities.

    The parameter severities should be passed an iterable of severity
    constants from this module.
    """
    def __init__(self, issuer, index, severities):
        super(MultiSeverityAlarm, self).__init__(issuer, index)
        self._severities = {severity: AlarmState(issuer, index, severity) for
                            severity in severities}

    def set(self, severity):
        """Send one of the alarm's raised states to the alarm agent.

        The severity must be one of the severity constants defined in this
        module. If this alarm cannot be raised with that severity, a KeyError
        is raised."""
        try:
            self._last_state_raised = self._severities[severity]
        except KeyError:
            _log.error('Attempted to raise incorrect alarm state %s',
                       severity)
            raise

        self.re_sync()


class AlarmState(object):
    """One of an alarm's possible states."""
    def __init__(self, issuer, index, severity):
        self.issuer = issuer
        self.index = index
        self.severity = severity

    def issue(self):
        """Tell the alarm agent that this is the current state of the alarm."""
        identifier = '{}.{}'.format(self.index, self.severity)
        _issue_alarm(self.issuer, identifier)


def _issue_alarm(process, identifier):
    """Attempt to send an alarm to the alarm agent.

    This function will time out after 2s.
    """
    # Clearwater nodes all have clearwater-infrastructure installed.
    # It includes a command-line script that can be used to issue an alarm.
    # We import the function used by the script and re-use it.
    #
    # See https://github.com/Metaswitch/clearwater-infrastructure/blob/master/clearwater-infrastructure/usr/share/clearwater/bin/alarms.py
    # for the target module.
    global _sendrequest
    if _sendrequest is None:
        try: # pragma: no cover
            # We can't rely on this file being present in unit tests so don't
            # test this clause.
            file, pathname, description = imp.find_module("alarms", ["/usr/share/clearwater/bin"])
            mod = imp.load_module("alarms", file, pathname, description)
            _sendrequest = mod.sendrequest
            _log.info("Imported /usr/share/clearwater/bin/alarms.py")
        except ImportError:
            _log.error("Could not import /usr/share/clearwater/bin/alarms.py, alarms will not be sent")

    if _sendrequest:
        _sendrequest(["issue-alarm", process, identifier])
