# -*- coding: utf-8 -*-
"""
tsurf.utils.settings
~~~~~~~~~~~~~~~~~~~~

This module defines various utility functions for dealing with vim variables.
"""

import vim


prefix = 'g:tsurf_'


def set(name, value):
    """To set a vim variable to a given value."""
    if isinstance(value, basestring):
        val = "'{0}'".format(value)
    elif isinstance(value, bool):
        val = "{0}".format(1 if value else 0)
    else:
        val = value

    vim.command("let {0} = {1}".format(prefix + name, val))


def get(name, type=None):
    """To get the value of a vim variable."""
    rawval = vim.eval(prefix + name)
    if type is bool:
        return False if rawval == '0' else True
    elif type is int:
        return int(rawval)
    elif type is float:
        return float(rawval)
    else:
        return rawval
