#!/usr/bin/env python3
"""
measuring tools
"""
import datetime as dt

from EXIFnaming.helpers.date import giveDatetime, newdate

__all__ = ["Clock", "TimeJumpDetector", "DirChangePrinter"]


class DirChangePrinter:

    def __init__(self, directory):
        self.counter = 0
        self.current_dir = directory

    def update(self, directory):
        if not self.current_dir == directory:
            print("updated %4d tags in %s" % (self.counter, self.current_dir))
            self.counter = 0
            self.current_dir = directory
        self.counter += 1

    def finish(self):
        print("updated %4d tags in %s" % (self.counter, self.current_dir))


class Clock:

    def __init__(self):
        self.timebegin = dt.datetime.now()

    def finish(self):
        timedelta = dt.datetime.now() - self.timebegin
        print("elapsed time: %2d min, %2d sec" % (int(timedelta.seconds / 60), timedelta.seconds % 60))


class TimeJumpDetector:
    _lowJump = dt.timedelta(minutes=20)
    _bigJump = dt.timedelta(minutes=60)
    _is_first = True

    def __init__(self):
        self.time = giveDatetime()
        self.time_old = giveDatetime()
        self.timedelta = self.time - self.time_old

    def isJump(self, time, file_number: int) -> bool:
        self.time_old = self.time
        self.time = time
        self.timedelta = self.time - self.time_old
        is_time_jump = self.timedelta > self._bigJump or (self.timedelta > self._lowJump and file_number > 100)
        is_new_date = newdate(self.time, self.time_old)
        return_val = not self._is_first and (is_time_jump or is_new_date)
        self._is_first = False
        return return_val
