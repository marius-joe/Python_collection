#!/usr/bin/env python3.7

# ******************************************
#  Dev:  marius-joe
# ******************************************
#  General Utilities
#  v1.1.5
# ******************************************

"""General utility functions"""


import os, sys, subprocess
import logging
import re
from stat import ST_DEV, ST_INO, ST_MTIME
import contextlib

# dill is an advanced version of pickle
import dill as pickle  # req: https://github.com/uqfoundation/dill
import time
import json
import fire  # req: https://github.com/google/python-fire



# converts minutes to 00:00 hours
def convert_minutes_to_dayHours(minutes):
    # the time can also be on the next day, so use the mod operator
    return "{:02d}:{:02d}".format(*divmod(minutes % (24 * 60), 60))


# retrieves the stored selection of given options from a binary code or the converted value of a decimal number
# example:
# options = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
# selection_code = 62 -> 0111110
# selection = ["Tuesday","Wednesday","Thursday","Friday","Saturday"]
def get_selection_from_binaryCode(selection_code, options):
    selection = []
    # allow zero as a selection_code
    if selection_code is not None:
        if isinstance(selection_code, str):
            binCode = selection_code
        elif isinstance(selection_code, int):
            binCode = bin(selection_code)[2:]
        len_binCode = len(binCode)
        # check every digit of the binary code, if it sets the corresponding item in the available options to 'True'
        # go backwards through the binary code to retrieve the selected options in the correct order

        # toDo: test len_binCode-1
        for i in range(len_binCode):
            if binCode[len_binCode - 1 - i] == "1":
                selection.append(options[i])
    return selection


# to return [] when splitting an empty string with a specified separator (normal split() returns [''])
def xSplit(str, delim=" "):
    return [x for x in str.split(delim) if x]


# get intersection between two dictionaries: same keys with the same values
def get_intersection_dicts(objSmall, objBig):
    intersection = {}
    for key,value in objSmall.items():
        if (deepGet_safe(objBig, key) == value):
            intersection[key] = value
    return intersection


# toDo
# geht noch nicht
# get difference between two dictionaries: filter out the matching keys,value pairs
def get_difference_dicts(objSmall, objBig):
    difference = {}
    for key,value in objSmall.items():
        if (deepGet_safe(objBig, key) != value):
            difference[key] = value
    return difference


# ----------------------------------------------------
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
# ----------------------------------------------------


# toDo: has to be improved for empty lists and dicts
def remove_unwantedItems(myDict, unwanted_values):
    # unwanted_values = ["", None, {}, []])
    unwanted_keys = []
    for key, value in myDict.items():
        if isinstance(value, dict):
            if not value:
                if {} in unwanted_values:
                    unwanted_keys.append(key)  # nested dict is empty
            else:
                remove_unwantedItems(
                    value, unwanted_values
                )  # dive into the nested structure
        # nested list is empty
        elif isinstance(value, list) and not value and [] in unwanted_values:
            unwanted_keys.append(key)
        # deal with values of only whitespaces
        elif isinstance(value, str):
            value = value.strip()
        # to keep 0 values we have to do the unwanted_values check like this
        elif any([value is i for i in unwanted_values]):
            unwanted_keys.append(key)
    # delete keys in a seperate step because deleting while iterating over dict.items is not allowed
    for key in unwanted_keys:
        del myDict[key]


def get_line_seperator():
    return (
        "------------------------------------------------------------------------------"
    )


# v1.1
# use no indent for compact form
def get_jsonStr(obj, encoding='utf-8', indent=None):
    if not indent:
        separators = (',', ':') # create the most compact output
    else:
        separators = (',', ': ')
    return json.dumps(
        obj, ensure_ascii=(encoding == 'ascii'), indent=indent, separators=separators
    )


def get_jsonStr_escaped(obj, encoding='utf-8', indent=None):
    json_str = get_jsonStr(obj, encoding, indent)
    return json_str[1:-1]


def sleep_ms(delay_ms):
    time.sleep(float(delay_ms) / 1000.0)  # conversion for milliseconds


def get_timedelta_h_min(td):
    minutes, seconds = divmod(td.total_seconds(), 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours:.0f}:{minutes:02.0f}min"


def get_timedelta_d_h_min(td):
    minutes, seconds = divmod(td.total_seconds(), 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    optDays = f"{days:.0f}d " if days > 0 else ""
    return f"{optDays}{hours:.0f}:{minutes:02.0f}h"


def get_timedelta_min(td):
    return int((td).total_seconds() / 60)


def get_singular_plural(counter, word):
    if counter == 1:
        return word
    else:
        return word + "s"


def deepGet_safe(myDict, *keys):
    """
    Get values in a nested dictonary tree easy and safe without errors.
    If a value doesn't exist, return None
    """
    for key in keys:
        try:
            value = myDict[key]
            if not value is None:
                myDict = value  # for next iteration
            else:
                # key exists, but has a Null value
                value = ""
                break
        except:
            value = None
            break
    return value


def xStr(value, default=''):
    """
    Extended str() adding a default result, if the input is None
    """
    return default if (value is None) else str(value)


def get_os_executable_path(path):
    import platform
    if platform.system() == 'Windows':
        newPath = path + ".exe"
    else:  # 'Linux' or 'Darwin' (Mac)
        newPath = path
    return newPath


def write_text(text):
    return text


# toDo: in testing
if __name__ == "__main__":
    # grant command line access to some functions of this module
    # https://github.com/google/python-fire/blob/master/docs/using-cli.md
    public_functions = {"write_text": write_text}
    sys.exit(fire.Fire(public_functions))

