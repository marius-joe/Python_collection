#!/usr/bin/env python3.7

# ******************************************
#  Dev:  marius-joe
# ******************************************
#  Microsoft Office Utilities
#  v0.3.4
# ******************************************

# Under Construction

"""Office utility functions"""

import os, subprocess, sys
import logging
import re
from stat import ST_DEV, ST_INO, ST_MTIME
import json

import win32com.client as win32  # req

from . import utils_io


# v0.4
# Req: Microsoft Excel application
class ExcelDoc_Editor(utils_io.FileProcessor):
    """
    Editor that changes Values in Microsoft Excel documents to another desired format
    If the input is a folder, all of the Excel documents in that folder will be proccessed.
    """

    def __init__(
        self,
        path_input,
        path_output_folder,
        replacements,
        restrict_ext=".xlsx",
        xlFileFormat="xlWorkbookDefault",
    ):
        super().__init__(path_input, path_output_folder, restrict_ext)

        self.output_files = []
        self.replacements = replacements
        self.num_sheets_processed = 0

        self.xlFileFormat = xlFileFormat

        self.excel_app = ExcelControl().session
        if self.excel_app:
            self.excel_app.DisplayAlerts = False
            self.process_excel_documents(
                path_input,
                self.path_output_folder,
                self.restrict_ext,
                self.xlFileFormat,
            )
            self.excel_app.DisplayAlerts = True
            logging.info("")
        else:
            msg = "Connection to the Excel application could not be established !"
            logging.info(msg)

    # overwrite
    def _file_actions(self, path_file):
        file_name = os.path.basename(path_file)


# v0.8
# Req: Microsoft Office application to be controlled
class OfficeAppControl:
    """
    Connector for Microsoft Office applications
    """

    def __init__(self, app):
        self.session = self._create_appSession(app)
        if not self.session:
            msg = f"Connection to the Office application  [{app}]  could not be established !"
            logging.info(msg)

    # Try to open win32com instance for named application. If it's not successful return the error message
    def _create_appSession(self, app):
        # Better: check if the office app is running and restart it first to get a clean session
        errorCode = ""
        try:
            session = win32.gencache.EnsureDispatch(f"{app}.Application")
        except (Exception, errorCode):
            logging.info(errorCode)
        return session

    def shutdown(self):
        self.session.Quit()
        self.session = None

