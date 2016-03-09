# @file test_alarms.py
#
# project clearwater - ims in the cloud
# copyright (c) 2013  metaswitch networks ltd
#
# this program is free software: you can redistribute it and/or modify it
# under the terms of the gnu general public license as published by the
# free software foundation, either version 3 of the license, or (at your
# option) any later version, along with the "special exception" for use of
# the program along with ssl, set forth below. this program is distributed
# in the hope that it will be useful, but without any warranty;
# without even the implied warranty of merchantability or fitness for
# a particular purpose.  see the gnu general public license for more
# details. you should have received a copy of the gnu general public
# license along with this program.  if not, see
# <http://www.gnu.org/licenses/>.
#
# the author can be reached by email at clearwater@metaswitch.com or by
# post at metaswitch networks ltd, 100 church st, enfield en2 6bq, uk
#
# special exception
# metaswitch networks ltd  grants you permission to copy, modify,
# propagate, and distribute a work formed by combining openssl with the
# software, or a work derivative of such a combination, even if such
# copying, modification, propagation, or distribution would otherwise
# violate the terms of the gpl. you must comply with the gpl in all
# respects for all of the code used other than openssl.
# "openssl" means openssl toolkit software distributed by the openssl
# project and licensed under the openssl licenses, or a work based on such
# software and licensed under the openssl licenses.
# "openssl licenses" means the openssl license and original ssleay license
# under which the openssl project distributes the openssl toolkit software,
# as those licenses appear in the file license-openssl.
import unittest
import mock
import threading
import time
import logging

_log = logging.getLogger()

from metaswitch.common.alarms import (AlarmState,
                                      BaseAlarm,
                                      Alarm,
                                      MultiSeverityAlarm,
                                      CLEARED,
                                      _AlarmManager)


class TimeoutError(Exception):
    """Timed out waiting for the run loop to complete."""


class TestAlarmManager(_AlarmManager):
    """AlarmManager with extra test function."""

    def loop_done_hook(self):
        """Callback to notify the test code that the loop has completed."""
        with self._condition:
            self._awake = False
            self._condition.notify()

    def wake_up(self):
        """Force the alarm manager to cycle through its run loop.

        Wait up to 5s seconds for the run loop to complete. If it does not,
        then raise a TimeoutError."""
        with self._condition:
            self._awake = True
            self._condition.notify()
            self._condition.wait(5)
            if self._awake:
                raise TimeoutError

    def safe_terminate(self):
        """Terminate on another thread to avoid hanging."""
        terminate_thread = threading.Thread(target=self.terminate)
        terminate_thread.daemon = True
        terminate_thread.start()
        terminate_thread.join(5)


class TestAlarmState(unittest.TestCase):
    @mock.patch('metaswitch.common.alarms._sendrequest')
    def test_issue_alarm(self, mock_sendrequest):
        """Alarm states can be issued."""
        alarm_state = AlarmState('TestIssuer', 1000, 6)
        alarm_state.issue()
        mock_sendrequest.assert_called_once_with(['issue-alarm',
                                                  'TestIssuer',
                                                  '1000.6'])


class TestBaseAlarm(unittest.TestCase):
    @mock.patch('metaswitch.common.alarms._sendrequest')
    def test_clear_base_alarm(self, mock_sendrequest):
        """Alarms can be cleared."""
        base_alarm = BaseAlarm('TestIssuer', 1000)
        base_alarm.clear()
        mock_sendrequest.assert_called_once_with(['issue-alarm',
                                                  'TestIssuer',
                                                  '1000.1'])


class TestAlarm(unittest.TestCase):
    @mock.patch('metaswitch.common.alarms._sendrequest')
    def test_set_alarm(self, mock_sendrequest):
        """Alarms can be set."""
        alarm = Alarm('TestIssuer', 1000, 3)
        alarm.set()
        mock_sendrequest.assert_called_once_with(['issue-alarm',
                                                  'TestIssuer',
                                                  '1000.3'])


    @mock.patch('metaswitch.common.alarms._sendrequest')
    def test_clear_alarm(self, mock_sendrequest):
        """Alarm can be cleared after they are set."""
        alarm = Alarm('TestIssuer', 1000, 3)
        alarm.set()
        alarm.clear()
        mock_sendrequest.assert_called_with(['issue-alarm',
                                             'TestIssuer',
                                             '1000.1'])


class TestMultiSeverityAlarm(unittest.TestCase):
    @mock.patch('metaswitch.common.alarms._sendrequest')
    def test_set_multi_severity_alarm(self, mock_sendrequest):
        """Multiple severities can be raised."""
        alarm = MultiSeverityAlarm('TestIssuer', 1000, [3, 6])
        alarm.set(3)
        mock_sendrequest.assert_called_once_with(['issue-alarm',
                                                  'TestIssuer',
                                                  '1000.3'])
        mock_sendrequest.reset_mock()
        alarm.set(6)
        mock_sendrequest.assert_called_once_with(['issue-alarm',
                                                  'TestIssuer',
                                                  '1000.6'])

    @mock.patch('metaswitch.common.alarms._sendrequest')
    def test_bad_multi_severity_alarm(self, mock_sendrequest):
        """Attempting to raise an alarm with the wrong severity fails."""
        alarm = MultiSeverityAlarm('TestIssuer', 1000, [3, 6])
        self.assertRaises(KeyError, alarm.set, 5)


class TestAlarmManagerGetAlarm(unittest.TestCase):
    @mock.patch('threading.Condition', autospec=True)
    @mock.patch('metaswitch.common.alarms.atexit', autospec=True)
    def test_basic_get_alarm(self, mock_atexit, mock_condition):
        """We can get an alarm from the manager."""
        alarm_manager = _AlarmManager()

        # We don't want to start it re-sending alarms.
        with mock.patch.object(alarm_manager, 'start') as mock_start:
            alarm = alarm_manager.get_alarm('TestIssuer', (1000, 1, 6))

        # Check that the alarm works as expected.
        alarm.set()
        alarm.clear()

        # Check that the alarm_manager tried to start and registered for
        # cleanup.
        mock_start.assert_called_once_with()
        mock_atexit.register.assert_called_once_with(alarm_manager.terminate)

    @mock.patch('threading.Condition', autospec=True)
    @mock.patch('metaswitch.common.alarms.atexit', autospec=True)
    def test_multi_get_alarm(self, mock_atexit, mock_condition):
        """We can get a multi-severity alarm from the manager."""
        alarm_manager = _AlarmManager()

        # We don't want to start it re-sending alarms.
        with mock.patch.object(alarm_manager, 'start') as mock_start:
            alarm = alarm_manager.get_alarm('TestIssuer', (1000, 1, 2, 6))

        # Check that the alarm works as expected.
        alarm.set(6)
        alarm.clear()

        # Check that the alarm_manager tried to start and registered for
        # cleanup.
        mock_start.assert_called_once_with()
        mock_atexit.register.assert_called_once_with(alarm_manager.terminate)

    @mock.patch('threading.Condition', autospec=True)
    @mock.patch('metaswitch.common.alarms.atexit', autospec=True)
    def test_bad_alarm(self, mock_atexit, mock_condition):
        """The alarm manager doesn't create bad alarms."""
        alarm_manager = _AlarmManager()

        # We don't want to start it re-sending alarms.
        with mock.patch.object(alarm_manager, 'start'):
            # No data.
            self.assertRaises(Exception,
                              alarm_manager.get_alarm,
                              'TestIssuer',
                              ())
            # No severities.
            self.assertRaises(Exception,
                              alarm_manager.get_alarm,
                              'TestIssuer',
                              (1000))
            # Only cleared severity.
            self.assertRaises(Exception,
                              alarm_manager.get_alarm,
                              'TestIssuer',
                              (1000, CLEARED))


class TestAlarmManagerReSync(unittest.TestCase):

    @mock.patch('metaswitch.common.alarms._sendrequest')
    @mock.patch('metaswitch.common.alarms.atexit', autospec=True)
    def test_terminate(self, mock_atexit, mock_sendrequest):
        """Check that alarm manager termination takes under 5s.

        5s is a tolerable period to wait on shutdown. Any longer will start
        to be noticed.

        If this test fails, some stack traces may be printed to screen
        when the current test process exits."""
        # The strategy for this test is to kick off termination in another
        # thread, then wait 5s for it to finish. If it does not terminate,
        # we can't guarantee that we can clean it up, so just leave it
        # running.
        alarm_manager = _AlarmManager()
        alarm_manager.start()

        terminate_thread = threading.Thread(target=alarm_manager.terminate)

        # Don't let the test hang due to this thread remaining.
        terminate_thread.daemon = True
        terminate_thread.start()

        # Give the manager time to get started.
        time.sleep(0.1)

        terminate_thread.join(5)
        self.assertFalse(terminate_thread.is_alive())

    @unittest.skip("Issue #44")
    @mock.patch('metaswitch.common.alarms.monotonic')
    @mock.patch('metaswitch.common.alarms._sendrequest')
    @mock.patch('metaswitch.common.alarms.atexit', autospec=True)
    def test_resync(self, mock_atexit, mock_sendrequest, mock_monotonic):
        """Check that the alarm manager sends alarms after 30s."""
        try:
            # Start at 0 during initialization.
            # Check that we account for a 5s delay in getting started.
            # After 29s, no alarms should be raised.
            # After 30s, they should be.
            # Give one more value to allow the alarm_manager to start
            # waiting again.
            mock_monotonic.side_effect = [0,
                                          5,
                                          29,
                                          30,
                                          35]

            alarm_manager = TestAlarmManager()

            # Get an alarm to prompt the alarm manager to start.
            alarm_manager.get_alarm('DummyIssuer', (1000, CLEARED, 6))

            alarm_manager.wake_up()
            self.assertFalse(mock_sendrequest.called)

            alarm_manager.wake_up()
            self.assertTrue(mock_sendrequest.called)

        finally:
            alarm_manager.safe_terminate()

    @unittest.skip("Issue #44")
    @mock.patch('metaswitch.common.alarms.monotonic')
    @mock.patch('metaswitch.common.alarms._sendrequest')
    @mock.patch('metaswitch.common.alarms.atexit', autospec=True)
    def test_skipped_resync(self, mock_atexit, mock_sendrequest, mock_monotonic):
        """Check that the alarm manager copes with missed resyncs."""
        try:
            # Start at 0 during initialization.
            # 35s is longer than the re-sync interval!
            # After 59s, no alarms should be raised.
            # After 60s, they should be.
            # Give one more value to allow the alarm_manager to start
            # waiting again.
            mock_monotonic.side_effect = [0,
                                          35,
                                          59,
                                          60,
                                          65]

            alarm_manager = TestAlarmManager()

            # Get an alarm to prompt the alarm manager to start.
            alarm_manager.get_alarm('DummyIssuer', (1000, CLEARED, 6))

            alarm_manager.wake_up()
            self.assertFalse(mock_sendrequest.called)

            alarm_manager.wake_up()
            self.assertTrue(mock_sendrequest.called)

        finally:
            alarm_manager.safe_terminate()

    @mock.patch('metaswitch.common.alarms._sendrequest')
    @mock.patch('metaswitch.common.alarms.atexit', autospec=True)
    def test_start_once(self, mock_atexit, mock_sendrequest):
        """Test that the alarm manager thread starts once and only once."""
        alarm_manager = TestAlarmManager()

        with mock.patch.object(alarm_manager, 'start') as mock_start:
            alarm_manager.get_alarm('DummyIssuer', (1000, CLEARED, 4))
            alarm_manager.get_alarm('DummyIssuer', (2000, CLEARED, 6))

        mock_start.assert_called_once_with()
