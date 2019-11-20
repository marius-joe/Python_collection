#!/usr/bin/env python3.7

# ******************************************
#  Dev:  marius-joe
# ******************************************
#  Logging Utilities
#  v1.0.7
# ******************************************

"""Utility functions for logging"""

import os, sys
import logging
from logging.handlers import BaseRotatingHandler
from logging.handlers import TimedRotatingFileHandler
from logging.handlers import RotatingFileHandler
from stat import ST_DEV, ST_INO, ST_MTIME
import re
import time
import fire  # req


# v1.1
def setup_logging(path_file, console=True, level=logging.INFO, file_log_interval=None, max_size_KB=500):
    # create the files directory path if it doesn't exist
    ensure_path(os.path.dirname(path_file))

    rootLogger = logging.getLogger()
    rootLogger.setLevel(level)

    # define a handler which writes messages with the specified level or higher to file
    if file_log_interval:
        # time limited log
        file_out = TimedRotatingFileHandler_keepExt(
            path_file, when=file_log_interval, backupCount=6, keepExtension=True
        )
    else:
        # size limited log
        file_out = RotatingFileHandler_keepExt(
            path_file, maxBytes=1024 * max_size_KB, backupCount=3, keepExtension=True
        )

    file_out.setLevel(level)
    formatter = logging.Formatter("%(message)s")
    file_out.setFormatter(formatter)
    rootLogger.addHandler(file_out)

    if console:
        # define a handler which writes messages with the specified level or higher to the sys.stderr
        console_out = logging.StreamHandler()
        console_out.setLevel(level)
        formatter = logging.Formatter("%(message)s")
        console_out.setFormatter(formatter)
        rootLogger.addHandler(console_out)


# inherits TimedRotatingFileHandler from python library and add keepExtension option
class TimedRotatingFileHandler_keepExt(TimedRotatingFileHandler):
    """
    Handler for logging to a file, rotating the log file at certain timed
    intervals.

    If backupCount is > 0, when rollover is done, no more than backupCount
    files are kept - the oldest ones are deleted. By default the timestamp
    will be the last element in the filename. With keepExtension = True
    the file extension can be kept at the end of the backup file's name
    to support file associations in Windows.
    """

    def __init__(self,filename,when="h",interval=1,backupCount=0,encoding=None,delay=False,utc=False,atTime=None,keepExtension=False):
        super().__init__(filename,when,interval,backupCount,encoding,delay,utc,atTime)
        self.keepExtension = keepExtension

    # overwrite
    def getFilesToDelete(self):
        """
        Determine the files to delete when rolling over.

        More specific than the earlier method, which just used glob.glob().
        """
        dirName, baseName = os.path.split(self.baseFilename)
        fileNames = os.listdir(dirName)
        result = []
        root, ext = os.path.splitext(baseName)
        root += "."
        plen = len(root)
        elen = len(ext)
        for fileName in fileNames:
            isRotatorFile = False
            if fileName[:plen] == root:
                if (
                    ext and self.keepExtension
                ):  # rotator suffix is in the filenames middle
                    # if the basename has an extension and keepExtension is True,
                    # the filename extension has to match this
                    if fileName[-elen:] == ext:
                        suffix = fileName[plen:-elen]
                        if self.extMatch.match(suffix):
                            isRotatorFile = True
                else:  # rotator suffix is at the filenames end
                    suffix = fileName[
                        plen + elen :
                    ]  # if there is no ext, elen will be 0 anyway
                    if self.extMatch.match(suffix):
                        isRotatorFile = True
            if isRotatorFile:
                result.append(os.path.join(dirName, fileName))
        if len(result) < self.backupCount:
            result = []
        else:
            result.sort()
            result = result[: len(result) - self.backupCount]
        return result

    # overwrite
    def doRollover(self):
        """
        do a rollover; in this case, a date/time stamp is appended to the filename
        when the rollover happens.  However, you want the file to be named for the
        start of the interval, not the current time.  If there is a backup count,
        then we have to get a list of matching filenames, sort them and remove
        the one with the oldest suffix.
        """
        if self.stream:
            self.stream.close()
            self.stream = None
        # get the time that this sequence started at and make it a TimeTuple
        currentTime = int(time.time())
        summerTime_now = time.localtime(currentTime)[-1]
        t = self.rolloverAt - self.interval
        if self.utc:
            timeTuple = time.gmtime(t)
        else:
            timeTuple = time.localtime(t)
            summerTime_then = timeTuple[-1]
            if summerTime_now != summerTime_then:
                if summerTime_now:
                    addend = 3600
                else:
                    addend = -3600
                timeTuple = time.localtime(t + addend)
        if self.keepExtension:
            root, ext = os.path.splitext(self.baseFilename)
            rotation_filename = root + "." + time.strftime(self.suffix, timeTuple) + ext
        else:
            rotation_filename = (
                self.baseFilename + "." + time.strftime(self.suffix, timeTuple)
            )
        path_dest = self.rotation_filename(rotation_filename)
        if os.path.exists(path_dest):
            os.remove(path_dest)
        self.rotate(self.baseFilename, path_dest)
        if self.backupCount > 0:
            for s in self.getFilesToDelete():
                os.remove(s)
        if not self.delay:
            self.stream = self._open()
        newRolloverAt = self.computeRollover(currentTime)
        while newRolloverAt <= currentTime:
            newRolloverAt = newRolloverAt + self.interval
        # If summer time (daylight saving time) changes and midnight or weekly rollover, adjust for this.
        if (self.when == "MIDNIGHT" or self.when.startswith("W")) and not self.utc:
            summerTime_atRollover = time.localtime(newRolloverAt)[-1]
            if summerTime_now != summerTime_atRollover:
                if (
                    not summerTime_now
                ):  # summer time (daylight saving time) kicks in before next rollover, so we need to deduct an hour
                    addend = -3600
                else:  # summer time (daylight saving time) bows out before next rollover, so we need to add an hour
                    addend = 3600
                newRolloverAt += addend
        self.rolloverAt = newRolloverAt

# inherits RotatingFileHandler from python 3.6 and add keepExtension option
class RotatingFileHandler_keepExt(RotatingFileHandler):
    """
    Handler for logging to a set of files, which switches from one file
    to the next when the current file reaches a certain size.
    """

    def __init__(self,filename,mode="a",maxBytes=0,backupCount=0,encoding=None,delay=False,keepExtension=False):
        """
        Open the specified file and use it as the stream for logging.

        By default, the file grows indefinitely. You can specify particular
        values of maxBytes and backupCount to allow the file to rollover at
        a predetermined size.

        Rollover occurs whenever the current log file is nearly maxBytes in
        length. If backupCount is >= 1, the system will successively create
        new files with the same pathname as the base file, but with extensions
        ".1", ".2" etc. appended to it. For example, with a backupCount of 5
        and a base file name of "app.log", you would get "app.log",
        "app.log.1", "app.log.2", ... through to "app.log.5". The file being
        written to is always "app.log" - when it gets filled up, it is closed
        and renamed to "app.log.1", and if files "app.log.1", "app.log.2" etc.
        exist, then they are renamed to "app.log.2", "app.log.3" etc.
        respectively. With keepExtension = True the file extension can be kept
        at the end of the backup file's name to support file associations in Windows.

        If maxBytes is zero, rollover never occurs.
        """
        # If rotation/rollover is wanted, it doesn't make sense to use another
        # mode than 'a' - append. If for example 'w' - write were specified,
        # the logs from previous runs would be lost if the 'w' is respected,
        # because the log file would be truncated on each run.
        if maxBytes > 0: mode = "a"
        super().__init__(filename,mode,maxBytes,backupCount,encoding,delay)
        self.keepExtension = keepExtension

    # overwrite
    def doRollover(self):
        """
        Do a rollover, as described in __init__().
        """
        if self.stream:
            self.stream.close()
            self.stream = None
        if self.backupCount > 0:
            root, ext = os.path.splitext(self.baseFilename)
            for i in range(self.backupCount - 1, 0, -1):
                if ext and self.keepExtension:
                    rotation_filename1 = "%s.%d" % (root, i) + ext
                    rotation_filename2 = "%s.%d" % (root, i + 1) + ext
                else:
                    rotation_filename1 = "%s.%d" % (self.baseFilename, i)
                    rotation_filename2 = "%s.%d" % (self.baseFilename, i + 1)
                path_source = self.rotation_filename(rotation_filename1)
                path_dest = self.rotation_filename(rotation_filename2)
                if os.path.exists(path_source):
                    if os.path.exists(path_dest):
                        os.remove(path_dest)
                    os.rename(path_source, path_dest)
            if ext and self.keepExtension:
                rotation_filename = root + ".1" + ext
            else:
                rotation_filename = self.baseFilename + ".1"
            path_dest = self.rotation_filename(rotation_filename)
            if os.path.exists(path_dest):
                os.remove(path_dest)
            self.rotate(self.baseFilename, path_dest)
        if not self.delay:
            self.stream = self._open()


def get_line_seperator():
    return (
        "------------------------------------------------------------------------------"
    )


def ensure_path(path):
    import pathlib
    pathlib.Path(path).mkdir(parents=True, exist_ok=True)


def write_text(text):
    return text

def test_fire_cli(text):
    return text

if __name__ == '__main__':
    # grant command line access to some functions of this module
    # https://github.com/google/python-fire/blob/master/docs/using-cli.md
    public_functions = {
      'write_text': write_text
    }
    sys.exit(fire.Fire(public_functions))

