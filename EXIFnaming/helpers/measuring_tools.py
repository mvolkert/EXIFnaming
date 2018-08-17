#!/usr/bin/env python3
"""
measuring tools
"""
import datetime as dt

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
