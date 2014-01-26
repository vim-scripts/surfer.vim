# -*- coding: utf-8 -*-
"""
surfer.utils.settings
~~~~~~~~~~~~~~~~~~~~~

This module defines various utility functions for dealing with vim variables.
"""

from surfer.utils import v


prefix = 'g:surfer_'


def get(name, type=None):
    """To get the value of a vim variable."""
    rawval = v.eval(prefix + name)
    if type is bool:
        return False if rawval == '0' else True
    elif type is int:
        return int(rawval)
    elif type is float:
        return float(rawval)
    elif isinstance(rawval, basestring):
        return rawval.decode(v.encoding())
    else:
        return rawval
