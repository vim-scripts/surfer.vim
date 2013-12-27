# -*- coding: utf-8 -*-
"""
surfer.core
~~~~~~~~~~~

This module defines the Surfer class.
"""

import os
import vim

from surfer import ui
from surfer import finder
from surfer import services
from surfer import generator
from surfer.utils import v


class Surfer:

    def __init__(self):
        self.services = services.Services(self)
        self.generator = generator.TagsGenerator(self)
        self.finder = finder.TagsFinder(self, self.generator)
        self.ui = ui.UserInterface(self)

    def close(self):
        """To performs cleanup actions."""
        self.generator.close()

    def Open(self):
        """To open the Tag Surfer user interface."""
        self.ui.open()
