"""MIT License

Copyright (c) 2021 juergenH87, 2024 James Boulton

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE."""

import logging
import queue
import threading
import time
from typing import Callable

logger = logging.getLogger(__name__)


class Schedular:
    """A useful Schedular for for running jobs (Callbacks) at set intervals.
    """
    def __init__(self, name=""):
        self._timer_events = []
        self._async_jobs = []

        self._job_thread_end = threading.Event()
        logger.info("Starting Schedular async thread")
        self._job_thread_wakeup_queue = queue.Queue()
        self._job_thread = threading.Thread(target=self._async_job_thread, name=name)
        # A thread can be flagged as a "daemon thread". The significance of
        # this flag is that the entire Python program exits when only daemon
        # threads are left.
        self._job_thread.daemon = True
        self._job_thread.start()

    def _async_job_thread(self):
        """Asynchronous thread for handling various jobs

        This Thread handles various tasks:

        To construct a blocking wait with timeout the task waits on a
        queue-object. When other tasks are adding timer-events they can
        wakeup the timeout handler to recalculate the new sleep-time
        to awake at the new events.
        """

        while not self._job_thread_end.is_set():

            now = time.time()

            # next_wakeup = self.async_job_thread(now)
            next_wakeup = now + 5.0
            for job in self._async_jobs:
                next_wakeup = job(next_wakeup, now)

            # check timer events
            for event in self._timer_events:
                if event['deadline'] > now:
                    if next_wakeup > event['deadline']:
                        next_wakeup = event['deadline']
                else:
                    # deadline reached
                    # logger.debug("Deadline for event reached")
                    if event['callback'](event['cookie']):
                        # "true" means the callback wants to be called again
                        while event['deadline'] < now:
                            # just to take care of overruns
                            event['deadline'] += event['delta_time']
                        # recalc next wakeup
                        if next_wakeup > event['deadline']:
                            next_wakeup = event['deadline']
                    else:
                        # remove from list
                        self._timer_events.remove(event)

            time_to_sleep = next_wakeup - time.time()
            if time_to_sleep > 0:
                try:
                    self._job_thread_wakeup_queue.get(True, time_to_sleep)
                except queue.Empty:
                    # do nothing
                    pass

    def add_timer(self, delta_time: float, offset: float, callback: Callable, cookie=None):
        """Adds a callback to the list of timer events. The callback should return True
        if it wants to be called again.

        delta_time: float
            The time in seconds after which the event is to be triggered.

        offset: float
            The offset is added to the deltatime the first time the callback is run

        callback: Callable
            The callback function to call
        """

        d = {
            'delta_time': delta_time,
            'callback': callback,
            'deadline': (time.time() + delta_time + offset),
            'cookie': cookie,
            }

        self._timer_events.append(d)
        self.job_thread_wakeup()

    def remove_timer(self, callback: Callable):
        """Removes ALL entries from the timer event list for the given callback

        :param callback:
            The callback to be removed from the timer event list
        """
        for event in self._timer_events:
            if event['callback'] == callback:
                self._timer_events.remove(event)
        self.job_thread_wakeup()

    def add_async_job(self, callback):
        """Adds a callback to the list of async job
        """

        self._async_jobs.append(callback)
        self.job_thread_wakeup()

    def remove_async_job(self, callback: Callable):
        """Removes ALL entries from the async job list for the given callback

        :param callback:
            The callback to be removed from the timer event list
        """
        for job in self._async_jobs:
            if job == callback:
                self._async_jobs.remove(job)
        self.job_thread_wakeup()

    def job_thread_wakeup(self):
        """Wakeup the async job thread

        By calling this function we wakeup the asyncronous job thread to
        force a recalculation of next wakeup event.
        """
        self._job_thread_wakeup_queue.put(1)

    def stop(self):
        """Stops the N2k Connection background handling

        This Function explicitely stops the background handling of the N2k Connection.
        """
        self._job_thread_end.set()
        self.job_thread_wakeup()
        self._job_thread.join()
