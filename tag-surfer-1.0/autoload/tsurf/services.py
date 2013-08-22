# -*- coding: utf-8 -*-
"""
tsurf.services
~~~~~~~~~~~~~~

This module defines services used by any of the Tag Surfer components.
"""

import os
import vim

from tsurf.utils import v
from tsurf.utils import settings


class Services:

    def __init__(self, plug):
        self.plug = plug
        self.curr_project = CurrentProjectService()


class CurrentProjectService:

    def __init__(self):
        self.custom_root = ""
        self.root_cache = ""
        self.files_cache = []

    def get_files(self):
        """To get all files in the current project.

        The current working directory is derived from the path of
        the current open buffer. If `autochdir` is off this may differ
        from the output of the `:pwd` command.
        """
        files = []
        root = self.get_root()
        if root:
            cond1 = self.files_cache
            cond2 = cond1 and not self.files_cache[0].startswith(root)
            if not cond1 or cond2:
                # Get all files for the current project. Note that the `glob()`
                # function ignore everything that matches with any of the
                # wildcards listed in the `wildignore` option.
                # Note: the `glob()` function wants forward slashes even on
                # Windows
                expr = os.path.join(root, "**").replace("\\", "/")
                files = vim.eval('glob("{}")'.format(expr)).split("\n")
                self.files_cache = files
            else:
                files = self.files_cache

        return files

    def get_root(self):
        """To return the current project root."""
        if self.custom_root:
            return self.custom_root

        if not self.root_cache:
            root = self._find_project_root(v.cwd(),
                settings.get("root_markers"))
            self.root_cache = root

        return self.root_cache

    def set_root(self, root):
        """To set a custom root for the current project."""
        self.custom_root = root

    def _find_project_root(self, path, root_markers):
        """To find the the root of the current project.

        `markers` is a list of file/directory names the can be found
        in a project root directory.
        """
        if path == "/" or path.endswith(":\\"):
            return ""
        elif any(m in os.listdir(path) for m in root_markers):
            return path
        else:
            return self._find_project_root(os.path.dirname(path), root_markers)
