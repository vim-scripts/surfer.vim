# -*- coding: utf-8 -*-
"""
surfer.utils.v
~~~~~~~~~~~~~~

This module defines thin wrappers around vim commands and functions.
"""

import os
import vim


def echom(msg):
    """To display a message to the user via the command line."""
    vim.command('echom "[surfer] {0}"'.format(msg.replace('"', '\"')))


def echohl(msg, hlgroup):
    """To display a colored message to the user via the command line."""
    vim.command("echohl {}".format(hlgroup))
    echom(msg)
    vim.command("echohl None")


def cwd():
    """To return the current working directory. See :h getcwd()"""
    return vim.eval('getcwd()')


def highlight(hlgroup, patt):
    """To highlight with `hlgroup` every occurrence of `patt`."""
    vim.command("syn match {} /{}/".format(hlgroup, patt))


def redraw():
    """Little wrapper around the redraw command. See :h :redraw"""
    vim.command('redraw')


def focus_win(expr):
    """To go to the window numbered `expr`. See :wincmd"""
    if expr == "#":
        expr = vim.eval("winnr('#')")
    if expr == "$":
        expr = vim.eval("winnr('$')")
    vim.command('{0}wincmd w'.format(expr))


def cursor(target=None):
    """To move the cursor or return the current cursor position."""
    if not target:
        return vim.current.window.cursor
    vim.current.window.cursor = target


def bufwinnr(expr):
    """To return the number of the window for the buffer `expr`, where `expr`
    can be a number or a string. See :h bufwinnr()"""
    if isinstance(expr, (int, long)):
        return int(vim.eval("bufwinnr({})".format(expr)))
    return int(vim.eval("bufwinnr('{}')".format(expr)))


def bufname(nr=None):
    """To return the name of the buffer numbered `nr`. If no number is given,
    the name of the current buffer is returned. See :h bufname()"""
    if nr is None:
        return vim.current.buffer.name
    return vim.eval("bufname({})".format(nr))


def winnr(expr=None):
    """To return the number of current window or the number of the window
    `expr`, where `expr` can be # or %. See :h winnr()"""
    if expr is None:
        return int(vim.eval("winnr()"))
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


def buflisted(expr):
    """To check if a buffer is loaded. See :h buflisted()"""
    if isinstance(expr, basestring):
        return int(vim.eval("buflisted('{}')".format(expr)))
    return int(vim.eval("buflisted({})".format(expr)))


def buffers():
    """To return a list of all listed buffers."""
    fn = lambda buf: buf is not None and buflisted(buf)
    return filter(fn, (b.name for b in vim.buffers))


def len(expr):
    """To return the length of `expr`. See :h len()"""
    if isinstance(expr, basestring):
        return int(vim.eval('len("{}")'.format(expr.replace('"', '\"'))))
    return int(vim.eval('len("{}")'.format(expr)))
