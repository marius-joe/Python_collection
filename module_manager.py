#!/usr/bin/env python3.7

# ******************************************
#  Dev:  marius-joe
# ******************************************
#  Module Manager
#  v1.0.3
# ******************************************

"""
A module manager to load external utility modules from outside of the project path
- useful while developing multiple new projects which need the same utilities
"""

# usage to import /utils_general/utils_general.py from the parent directory

# Load my external general utils - include needed utils after dev via build script
# ----------------------------------------------------
# Get this scripts parent folder path
# - dot .. form would be only relativ to the current working directory

# from inspect import currentframe, getframeinfo

# C_Path_ThisModule = getframeinfo(currentframe()).filename
# C_Path_Python_Projects = os.path.dirname(C_Path_ThisModule)
# C_Folder_General_Utils = os.path.join(C_Path_Python_Projects, "utils_general")

# from utils.module_manager import ModuleManager

# ModuleManager = ModuleManager()
# utils_general = ModuleManager.import_module(C_Folder_General_Utils, "utils_general")

# ----------------------------------------------------


import os
from importlib import util

class ModuleManager():
    """
    Utils to load and handle Python modules
    """

    def import_module(self, path_module, module_name=''):   # v1.0
        """Import a python module from a path. 3.4+ only.
        e.g. general utils from outside of a package
        Does not call sys.modules[module_name] = path and sys.path.insert doesn't have to be misused like this:
        sys.path.insert(0, 'path/to/your/py_file') + import py_file"""

        if module_name:
            if not module_name.endswith('.py'): module_name += '.py'
            path_file = os.path.join(path_module, module_name)
        else:
            path_file = path_module

        try:
            file_name, file_ext = os.path.splitext(os.path.basename(path_file))
            spec = util.spec_from_file_location(module_name, path_file)
            module = util.module_from_spec(spec)
            spec.loader.exec_module(module)
        except Exception as ec:
            module = None
            print(ec)
        finally:
            return module




