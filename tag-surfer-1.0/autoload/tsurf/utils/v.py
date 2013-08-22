# -*- coding: utf-8 -*-
"""
tsurf.utils.v
~~~~~~~~~~~~~

This module defines thin wrappers around vim commands and functions.
"""

import os
import vim


def echom(msg):
    """To display a message to the user via the command line."""
    vim.command('echom "[tsurf] {0}"'.format(msg.replace('"', '\"')))


def echohl(msg, hlgroup):
    """To display a colored message to the user via the command line."""
    vim.command("echohl {}".format(hlgroup))
    echom(msg)
    vim.command("echohl None")


def cwd():
    """To return the current buffer directory if exists."""
    return vim.eval('getcwd()')


def synmatch(hlgroup, patt):
    """To highlight with `hlgroup` every occurrence of `patt`."""
    vim.command("syn match {} /{}/".format(hlgroup, patt))


def redraw():
    """Little wrapper around the redraw command."""
    vim.command('redraw')


def focus_win(winnr):
    """To go to the window with the given number."""
    vim.command('{0}wincmd w'.format(winnr))


def bufwinnr(expr):
    """To return the number of the window whose buffer is named or numbered
    'expr'."""
    if isinstance(expr, (int, long)):
        return int(vim.eval("bufwinnr({})".format(expr)))
    else:
        return int(vim.eval("bufwinnr('{}')".format(expr)))


def winnr(expr=None):
    """To return the current window number."""
    if expr is None:
        return int(vim.eval("winnr()"))
    else:
        return int(vim.eval("winnr('{}')".format(expr)))


def set_buffer(content):
    """To set the whole content of the current buffer at once."""
    if isinstance(content, list):
        vim.current.buffer[:] = content
    elif isinstance(content, basestring):
        vim.current.buffer[:] = content.split("\n")


def set_buffer_line(linenr, content):
    """To set a specific line of the current buffer."""
    vim.current.buffer[linenr] = content


def set_win_height(height):
    """To set the height of the current window."""
    vim.current.window.height = height


def set_win_cursor(line, col):
    """To set the cursor position in the current window."""
    vim.current.window.cursor = (line, col)


def bufloaded(expr):
    """To check if a buffer is loaded."""
    if isinstance(expr, (int, long)):
        return int(vim.eval("bufloaded({})".format(expr)))
    else:
        return int(vim.eval("bufloaded('{}')".format(expr)))


def buffers():
    """To return a list of all loaded buffers."""
    fn = lambda p: os.path.exists(p) and bufloaded(p)
    return filter(fn, (b.name for b in vim.buffers))
