#!/usr/bin/env python3.7

# ******************************************
#  Dev:  marius-joe
# ******************************************
#  Utilities for file operations
#  v0.9.3
# ******************************************

"""Utilities for file operations"""

import os, sys, subprocess
import logging
import re
from stat import ST_DEV, ST_INO, ST_MTIME
import contextlib

import json
import fire  # req: https://github.com/google/python-fire

# currently not working
#from . import utils_general

class FileProcessor:
    """
    File processor to do task on single files or the content of a folder.
    If the input is a folder, all of the files in that folder will be proccessed.
    """

    def __init__(self, path_input, path_output_folder, restrict_ext):
        self.path_output_folder = path_output_folder
        self.output_files = []
        self.restrict_ext = restrict_ext

    def _file_actions(self, path_file):
        pass  # implement actions here, when the FileProcessor is inherited

    def process_files(self, path_input, path_output_folder, restrict_ext):
        # For the case those values have been changed through a direct call of this function
        self.path_output_folder = path_output_folder
        self.xlFileFormat = xlFileFormat

        if os.path.exists(path_input):
            if os.path.isfile(path_input) and path_input.endswith(restrict_ext):
                path_file = path_input
                self._file_actions()

            elif os.path.isdir(path_input):
                for file_name in os.listdir(path_input):
                    if file_name.endswith(restrict_ext):
                        path_file = os.path.join(path_input, file_name)
                        self._file_actions()
        return self.output_files


def convert_utf8bom(path_file, path_new_file=""):
    if not path_new_file:
        path_new_file = path_file
    # reading with 'utf-8-sig' ensures, that also UTF-8-BOM can be processed
    with open(path_file, 'r', encoding='utf-8-sig') as fi:
        text = fi.read()
    with open(path_new_file, 'w', encoding='utf-8') as fo:
        fo.write(text)
    return path_new_file


def html_to_json(path_file, encoding='utf-8', indent=None):
    # reading with 'utf-8-sig' ensures, that also UTF-8-BOM can be processed
    with open(path_file, 'r', encoding='utf-8-sig') as fi:
        text = fi.read()
    html_json = {'html_code': text}
    file_path_root, file_ext = os.path.splitext(path_file)
    path_new_file = file_path_root + ".json"
    with open(path_new_file, 'w', encoding=encoding) as fo:
        json.dump(html_json, fo, ensure_ascii=False, indent=indent)
    return path_new_file

# besser in convert_html_to_json_escaped, da nur aus einzel script Teilen
# def create_jsonEscaped_text(text, path_new_file, encoding='utf-8', indent=None):
#     jsonEscaped_text = get_jsonStr_escaped(text, encoding, indent)
#     file_path_root, file_ext = os.path.splitext(path_file)
#     path_new_file = file_path_root + "_jsonEsc.txt"
#     write_file(path_new_file, jsonEscaped_text, mode='text')
#     return path_new_file

# what if html is not in a file
# extract the body from an html file
def extract_html_body(path_file):
    lines = read_file(path_file, mode='lines')
    html_body_lines = []
    toggle_copy_line = False
    for line in lines:
        line = line.strip()
        if line:
            if not toggle_copy_line:
                # read everything after the opening body tag
                toggle_copy_line = line.startswith("<body")
            else:
                # read until the closing body tag appears
                toggle_copy_line = not line.startswith("</body>")
                if toggle_copy_line: html_body_lines.append(line)




    # new lines have to be kept
    html_body = ' '.join(html_body_lines)
    # spaces between html tags can be deleted : <>  <>, maybe better with regex
    html_body = html_body.replace("> <", "><")
    return html_body


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


def jsonEscapeText(text, encoding='utf-8', indent=None):
    return get_jsonStr_escaped([text])


# v1.1
def write_file(path_file, output, mode='text', encoding='utf-8', indent=None):
    path_output = path_file
    #path_output = os.path.expanduser(path_file)
    if mode == 'json':
        content = get_jsonStr(output, encoding=encoding, indent=indent)
    elif isinstance(output, str):
        content = output
    elif isinstance(output, list):
        content = "".join(output)

    with open(path_output, 'w', encoding=encoding) as fo:
        fo.write(content)


# v1.3
# use utf-8-sig by default in case of BOM encoding
def read_file(path_file, mode='text', encoding='utf-8-sig'):
    import contextlib
    path_input = path_file
    #path_input = os.path.expanduser(path_file)
    result = None
    with contextlib.suppress(FileNotFoundError):
        with open(path_input, 'r', encoding=encoding) as fi:
            if mode == 'json':
                result = json.load(fi)
            else:
                text = fi.read()
                if mode == 'text':
                    result = text
                elif mode == 'words':
                    result = text.split(' ')
                elif mode == 'lines':
                    result = text.splitlines()
    return result


def ensure_path(path):
    import pathlib
    pathlib.Path(path).mkdir(parents=True, exist_ok=True)


def remove_if_exists(strPath):
    import contextlib
    with contextlib.suppress(FileNotFoundError):
        os.remove(strPath)


def addTxtToDict(dict, file_in):
    try:
        with open(file_in, 'r') as file:
            lines = file.read().splitlines()
            for line in lines:
                if not (line in dict):
                    dict[line] = ""  # info can be added here
        msg = "File successfully loaded :  " + file_in
        logging.info(msg)
    except:
        msg = "File not found :  " + file_in
        logging.info(msg)
    return dict


def write_text(text):
    return text


# toDo: in testing
if __name__ == "__main__":
    # grant command line access to some functions of this module
    # https://github.com/google/python-fire/blob/master/docs/using-cli.md
    public_functions = {"write_text": write_text}
    sys.exit(fire.Fire(public_functions))

