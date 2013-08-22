# -*- coding: utf-8 -*-
"""
tsurf.utils.misc
~~~~~~~~~~~~~~~~

This module defines various utilities.
"""


def millis(td):
    """To return the total milliseconds of a timedelta object."""
    return (td.days * 86400 + td.seconds) / 0.001  + (td.microseconds) * 0.001
