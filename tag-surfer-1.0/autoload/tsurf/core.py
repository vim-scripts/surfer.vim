# -*- coding: utf-8 -*-
"""
tsurf.core
~~~~~~~~~~

This module defines the TagSurfer class. This class serve two purpose:

  1) Defines the methods that are used by tsurf-owned vim commands.
  2) Creates all tsurf components and acts as a brigde among them.

"""

import os
import vim

from tsurf import ui
from tsurf import finder
from tsurf import services


class TagSurfer:

    def __init__(self):
        self.services = services.Services(self)
        self.finder = finder.Finder(self)
        self.ui = ui.UserInterface(self)

    def close(self):
        """To performs cleanup actions."""
        self.finder.close()

    def Open(self):
        """To open the Tag Surfer user interface."""
        self.ui.open()

    def SetProjectRoot(self, root=""):
        """To set the current project root to the current working directory or
        to the directory passed as argument."""
        home = os.path.expanduser("~")
        if root.startswith("~"):
            root = root.replace("~", home)
        elif root.startswith("$HOME"):
            root = root.replace("$HOME", home)
        self.services.curr_project.set_root(
                root if root else vim.eval("getcwd()"))

    def UnsetProjectRoot(self):
        """To unset the current project root."""
        self.services.curr_project.set_root("")
