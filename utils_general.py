#!/usr/bin/env python3.7

# ******************************************
#  Dev:  marius-joe
# ******************************************
#  General Utilities
#  v1.0.6
# ******************************************


"""Util functions"""

import os, sys, subprocess

import logging

from logging.handlers import BaseRotatingHandler
from logging.handlers import TimedRotatingFileHandler
from logging.handlers import RotatingFileHandler
import re
from stat import ST_DEV, ST_INO, ST_MTIME

# dill is an advanced version of pickle
import dill as pickle   # req: https://github.com/uqfoundation/dill
import time
import json
import fire     # req: https://github.com/google/python-fire
    
    
# -------------------------------------------------------------
# best performance if you give the longer string/list as second parameter so it is used for isdisjoint()
def hasIntersection_words(short_stringOrList, long_stringOrList):
    small_set = set(get_word_list(short_stringOrList))
    big_set = set(get_word_list(long_stringOrList))
    return not small_set.isdisjoint(big_set)


# best performance if you give the longer string/list as second parameter so it is used for intersection()
def get_intersection_words(short_stringOrList, long_stringOrList):
    small_set = set(get_word_list(short_stringOrList))
    big_set = set(get_word_list(long_stringOrList))
    return small_set.intersection(big_set)
    

def get_word_list(stringOrList):
    if isinstance(stringOrList, str):
        result = stringOrList.split()
    elif isinstance(stringOrList, list):
        result = stringOrList
    return result
# -------------------------------------------------------------


def write_json(path_output, object, encoding='utf-8', indent=4):
    with open(path_output, 'w', encoding=encoding) as fo:
        json.dump(object, fo, ensure_ascii=False, indent=indent)    
        
            
def write_file(path_output, strOrArr, encoding='utf-8'):
    import os
    outfile = os.path.expanduser(path_output)
    with open(outfile, 'w', encoding=encoding) as fo:
        if isinstance(strOrArr, str):
            fo.write(strOrArr)
        elif isinstance(strOrArr, list):
            # or Join without empty line at the end ?
            fo.writelines(f"{item}\n" for item in strOrArr)
            

def sleep_ms(delay_ms):
    time.sleep(float(delay_ms) / 1000.0)   # conversion for milliseconds


def get_timedelta_h_min(td):
    minutes, seconds = divmod(td.total_seconds(), 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours:02.0f}:{minutes:02.0f}"
    

def get_timedelta_min(td):
    return int((td).total_seconds()/60)


def get_singular_plural(counter, word):
    if counter == 1: return word
    else: return word + 's'
    

def ensure_path(path):
    import pathlib
    pathlib.Path(path).mkdir(parents=True, exist_ok=True)


def remove_if_exists(strPath):
    import contextlib
    with contextlib.suppress(FileNotFoundError): os.remove(strPath) 
    

def save_cookies(requests_cookiejar, path_file):
    with open(path_file + '.pkl', 'wb') as f:
        pickle.dump(requests_cookiejar, f)
    

def load_cookies(path_file):
    with open(path_file + '.pkl', 'rb') as f:
        return pickle.load(f)
        
        
def import_requestsCookies_to_selenium(requests_cookiejar, selenium_driver):
    cookies = [{'name': key, 'value': value} for key,value in requests_cookiejar.items()]
    for cookie in cookies:
        selenium_driver.add_cookie(cookie)
    
    
def deepget(myDict, *keys):
    for key in keys:
        try:
            value = myDict[key]
            if not value is None:
                myDict = value  # for next iteration
            else:
                # key exists, but has a Null value             
                value = ''
                break
        except:
            value = None
            break
    return value


# NoneType to String
def xStr(value, default=''):
    return default if (value is None) else str(value)
    

def addTxtToDict(dict, file_in):
    try:
        with open(file_in, 'r') as file:
            lines = file.read().splitlines()      
            for line in lines:
                if not (line in dict):
                    dict[line] = ''     # info can be added here
        msg = "File successfully loaded :  " + file_in
        logging.info(msg)
    except:
        msg = "File not found -> will be created :  " + file_in
        logging.info(msg)
    return dict
        
     
def get_os_executable_path(path):
    import platform
    if platform.system() == 'Windows':
        newPath = path + '.exe'
    else:   # 'Linux' or 'Darwin' (Mac)
        newPath = path 
    return newPath
    

def setup_logging(file_log, level=logging.INFO, interval=None):
    # set up logging to file
    rootLogger = logging.getLogger()
    rootLogger.setLevel(level)
       
    # define a handler which writes messages with set level or higher to file

    if interval:
        # time limited log
        file_out = TimedRotatingFileHandler_keepExt(file_log, when=interval, backupCount=6, keepExtension=True)   
    else:
        # size limited log
        max_size_KB = 500
        file_out = RotatingFileHandler_keepExt(file_log, maxBytes=1024*max_size_KB, backupCount=3, keepExtension=True) 

    file_out.setLevel(level)
    formatter = logging.Formatter('%(message)s')
    file_out.setFormatter(formatter)
    rootLogger.addHandler(file_out)   
                        
    # define a handler which writes messages with set level or higher to the sys.stderr
    console_out = logging.StreamHandler()
    console_out.setLevel(level)
    formatter = logging.Formatter('%(message)s')
    console_out.setFormatter(formatter)
    # add the handler to the root logger
    rootLogger.addHandler(console_out)
    
    
# inherits TimedRotatingFileHandler from python 3.6 and add keepExtension option
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
    def __init__(self, filename, when='h', interval=1, backupCount=0, encoding=None, delay=False, utc=False, atTime=None, keepExtension=False):
        BaseRotatingHandler.__init__(self, filename, 'a', encoding, delay)
        self.when = when.upper()
        self.backupCount = backupCount
        self.utc = utc
        self.atTime = atTime
        self.keepExtension = keepExtension
        # Calculate the real rollover interval, which is just the number of
        # seconds between rollovers.  Also set the filename suffix used when
        # a rollover occurs.  Current 'when' events supported:
        # S - Seconds
        # M - Minutes
        # H - Hours
        # D - Days
        # midnight - roll over at midnight
        # W{0-6} - roll over on a certain day; 0 - Monday
        #
        # Case of the 'when' specifier is not important; lower or upper case
        # will work.
        if self.when == 'S':
            self.interval = 1 # one second
            self.suffix = "%Y-%m-%d_%H-%M-%S"
            self.extMatch = r"^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}(\.\w+)?$"
        elif self.when == 'M':
            self.interval = 60 # one minute
            self.suffix = "%Y-%m-%d_%H-%M"
            self.extMatch = r"^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}(\.\w+)?$"
        elif self.when == 'H':
            self.interval = 60 * 60 # one hour
            self.suffix = "%Y-%m-%d_%H"
            self.extMatch = r"^\d{4}-\d{2}-\d{2}_\d{2}(\.\w+)?$"
        elif self.when == 'D' or self.when == 'MIDNIGHT':
            self.interval = 60 * 60 * 24 # one day
            self.suffix = "%Y-%m-%d"
            self.extMatch = r"^\d{4}-\d{2}-\d{2}(\.\w+)?$"
        elif self.when.startswith('W'):
            self.interval = 60 * 60 * 24 * 7 # one week
            if len(self.when) != 2:
                raise ValueError("You must specify a day for weekly rollover from 0 to 6 (0 is Monday): %s" % self.when)
            if self.when[1] < '0' or self.when[1] > '6':
                raise ValueError("Invalid day specified for weekly rollover: %s" % self.when)
            self.dayOfWeek = int(self.when[1])
            self.suffix = "%Y-%m-%d"
            self.extMatch = r"^\d{4}-\d{2}-\d{2}(\.\w+)?$"
        else:
            raise ValueError("Invalid rollover interval specified: %s" % self.when)

        self.extMatch = re.compile(self.extMatch, re.ASCII)
        self.interval = self.interval * interval # multiply by units requested
        # The following line added because the filename passed in could be a
        # path object (see Issue #27493), but self.baseFilename will be a string
        filename = self.baseFilename
        if os.path.exists(filename):
            t = os.stat(filename)[ST_MTIME]
        else:
            t = int(time.time())
        self.rolloverAt = self.computeRollover(t)
      
    def getFilesToDelete(self):
        """
        Determine the files to delete when rolling over.

        More specific than the earlier method, which just used glob.glob().
        """
        dirName, baseName = os.path.split(self.baseFilename)
        fileNames = os.listdir(dirName)
        result = []
        root, ext = os.path.splitext(baseName)
        root += '.'
        plen = len(root)
        elen = len(ext)
        for fileName in fileNames:
            isRotatorFile = False
            if fileName[:plen] == root:
                if ext and self.keepExtension:     # rotator suffix is in the filenames middle
                    # if the basename has an extension and keepExtension is True,
                    # the filename extension has to match this                    
                    if fileName[-elen:] == ext:     
                        suffix = fileName[plen:-elen]
                        if self.extMatch.match(suffix): isRotatorFile = True
                else:      # rotator suffix is at the filenames end
                    suffix = fileName[plen+elen:]   # if there is no ext, elen will be 0 anyway
                    if self.extMatch.match(suffix): isRotatorFile = True
            if isRotatorFile: result.append(os.path.join(dirName, fileName))
        if len(result) < self.backupCount:
            result = []
        else:
            result.sort()
            result = result[:len(result) - self.backupCount]
        return result

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
            rotation_filename = self.baseFilename + "." + time.strftime(self.suffix, timeTuple)
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
        if (self.when == 'MIDNIGHT' or self.when.startswith('W')) and not self.utc:
            summerTime_atRollover = time.localtime(newRolloverAt)[-1]
            if summerTime_now != summerTime_atRollover:
                if not summerTime_now:  # summer time (daylight saving time) kicks in before next rollover, so we need to deduct an hour
                    addend = -3600
                else:           # summer time (daylight saving time) bows out before next rollover, so we need to add an hour
                    addend = 3600
                newRolloverAt += addend
        self.rolloverAt = newRolloverAt
        
        
class RotatingFileHandler_keepExt(RotatingFileHandler):
    """
    Handler for logging to a set of files, which switches from one file
    to the next when the current file reaches a certain size.
    """
    def __init__(self, filename, mode='a', maxBytes=0, backupCount=0, encoding=None, delay=False, keepExtension=False):
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
        if maxBytes > 0:
            mode = 'a'
        BaseRotatingHandler.__init__(self, filename, mode, encoding, delay)
        self.maxBytes = maxBytes
        self.backupCount = backupCount
        self.keepExtension = keepExtension

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
            

def write_text(text):
    return text
    
    

if __name__ == '__main__':
    # grant command line access to some functions of this module
    # https://github.com/google/python-fire/blob/master/docs/using-cli.md
    public_functions = {
      'write_text': write_text
    }
    sys.exit(fire.Fire(public_functions))




