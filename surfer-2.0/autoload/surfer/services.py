# -*- coding: utf-8 -*-
"""
surfer.services
~~~~~~~~~~~~~~~

This module defines services used by any of the Surfer components.
"""

import os
import vim

from surfer.utils import v
from surfer.utils import settings


class Services:

    def __init__(self, plug):
        self.plug = plug
        self.project = CurrentProjectService()


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
        root = self.get_root()
        if not root:
            return []

        if not self.files_cache:
            # Get all files for the current project. Note that the `glob()`
            # function ignore everything that matches with any of the
            # wildcards listed in the `wildignore` option.
            # Note: the `glob()` function wants forward slashes even on
            # Windows
            expr = os.path.join(root, "**").replace("\\", "/")
            self.files_cache = vim.eval('glob("{}")'.format(expr)).split("\n")

        return self.files_cache

    def get_root(self):
        """To return the current project root."""
        if self.custom_root:
            return self.custom_root
        if not self.root_cache:
            self.root_cache = self._find_project_root(v.cwd(),
                settings.get("root_markers"))
        return self.root_cache

    def set_root(self, root):
        """To set a custom root for the current project."""
        self.custom_root = root

    def update_project_root(self):
        """To keep updated the project root whenever the user edits a buffer."""
        bufname = v.bufname()
        if bufname is None or not bufname.startswith(self.root_cache):
            self.files_cache = []
            self.root_cache = ""

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
