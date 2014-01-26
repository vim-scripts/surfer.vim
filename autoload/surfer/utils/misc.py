# -*- coding: utf-8 -*-
"""
surfer.utils.misc
~~~~~~~~~~~~~~~~~

This module defines various utilities.
"""

from surfer.utils import v


def as_byte_indexes(indexes, s):
    """To transform character indexes into byte indexes."""
    enc = v.encoding()
    idx = 0
    byte_indexes = []
    for i, c in enumerate(s):
        if i in indexes:
            byte_indexes.append(idx)
        idx += len(c.encode(enc))
    return byte_indexes


def millis(td):
    """To return the total milliseconds of a timedelta object."""
    return (td.days * 86400 + td.seconds) / 0.001  + (td.microseconds) * 0.001
