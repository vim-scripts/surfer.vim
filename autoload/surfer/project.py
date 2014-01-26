# -*- coding: utf-8 -*-
"""
surfer.project
~~~~~~~~~~~~~~

This module defines the Project class. This class represents the
current project, from the user perspective.
"""

from fnmatch import fnmatch
from os import walk, listdir
from unicodedata import normalize
from itertools import ifilter, imap
from os.path import isfile, dirname

from surfer.utils import v
from surfer.utils import settings


class Project:

    def __init__(self, plug):
        self.plug = plug
        self.root_cache = ""
        self.files_cache = []

    def get_files(self):
        """To get all files in the current project.

        The current working directory is derived from the path of
        the current open buffer.
        """
        root = self.get_root()
        if not root:
            return []

        if not self.files_cache:
            # Get all files of the current project.
            # XXX On OS X, if there is a directory whose name contains unicode
            # characters, glob("{root}/**") skips all files in that directory
            # except the first. (using os.walk in not a solution since it does
            # not filter files according to the `wildignore` vim option)
            files = v.call(u"glob('{}/**')".format(root)).split(u"\n")
            files = imap(lambda f: normalize("NFC", f), files)
            self.files_cache = filter(isfile, files)

        return self.files_cache

    def get_root(self):
        """To return the current project root."""
        if not self.root_cache:
            self.root_cache = self._find_root(v.cwd(), settings.get("root_markers"))
        return self.root_cache

    def update_root(self):
        """To keep updated the project root whenever the user edits a buffer."""
        bufname = v.bufname()
        if bufname is None or not bufname.startswith(self.root_cache):
            self.files_cache = []
            self.root_cache = u""

    def _find_root(self, path, root_markers):
        """To find the the root of the current project.

        `markers` is a list of file/directory names the can be found
        in a project root directory.
        """
        if path == u"/" or path.endswith(u":\\"):
            return U""
        elif any(m in listdir(path) for m in root_markers):
            return path
        else:
            return self._find_root(dirname(path), root_markers)
