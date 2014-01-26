# -*- coding: utf-8 -*-
"""
surfer.utils.v
~~~~~~~~~~~~~~

This module defines thin wrappers around vim commands and functions.
"""

import os
import vim
from unicodedata import normalize
from itertools import ifilter, imap


def eval(expr):
    """To evaluate the given expression.

    The caller is responsible for calling `decode()`.
    """
    return vim.eval(expr.encode(encoding()))


def opt(opt):
    """To return the value of a vim option."""
    val = eval("&{}".format(opt)).decode(encoding())
    if val.isdigit():
        return int(val)
    return val


def call(fun):
    """To return the value of a vim function."""
    val = eval(fun)
    if isinstance(val, basestring):
        val = val.decode(encoding())
        if val.isdigit():
            return int(val)
    return val


def exe(cmd):
    """To execute a vim command."""
    vim.command(cmd.encode(encoding()))


def echo(msg, hlgroup="", surfermsg=True):
    """To display a message to the user via the command line."""
    if hlgroup:
        exe(u"echohl {}".format(hlgroup))
    surfer = "[surfer] " if surfermsg else ""
    exe(u'echom "{}{}"'.format(surfer, msg).replace('"', '\"'))
    exe("echohl None")


def encoding():
    """To get the current encoding."""
    return vim.eval("&enc")


def cwd():
    """To return the current working directory. See :h getcwd()"""
    return call('getcwd()')


def highlight(hlgroup, patt):
    """To highlight with `hlgroup` every occurrence of `patt`."""
    exe(u"syn match {} /{}/".format(hlgroup, patt))


def redraw():
    """Little wrapper around the redraw command. See :h :redraw"""
    exe('redraw')


def focus_win(expr):
    """To go to the window numbered `expr`. See :wincmd"""
    if expr == "#":
        expr = call("winnr('#')")
    if expr == "$":
        expr = call("winnr('$')")
    exe(u'{}wincmd w'.format(expr))


def cursor(target=None):
    """To move the cursor or return the current cursor position."""
    if not target:
        return vim.current.window.cursor
    vim.current.window.cursor = target


def bufwinnr(expr):
    """To return the number of the window for the buffer `expr`, where `expr`
    can be a number or a string. See :h bufwinnr()"""
    if isinstance(expr, (int, long)):
        return call("bufwinnr({})".format(expr))
    return call(u"bufwinnr('{}')".format(expr))


def buffer(nr=None):
    """To return the the buffer numbered `nr`. If no number is given,
    the the current buffer is returned."""
    if nr is None:
        return vim.current.buffer
    for buf in vim.buffers:
        if buf and buf.number == nr:
            return buf


def bufname(nr=None):
    """To return the name of the buffer numbered `nr`. If no number is given,
    the name of the current buffer is returned."""
    current = vim.current.buffer
    if nr is None and current.name:
        return normalize("NFC", current.name.decode(encoding()))
    elif nr is not None:
        for buf in vim.buffers:
            if buf.number == nr and buf.name:
                return normalize("NFC", buf.name.decode(encoding()))


def bufnr(expr=None):
    """To return the number of the buffer `expr`."""
    if expr is None:
        expr = "%"
    return call(u"bufnr('{}')".format(expr))


def winnr(expr=None):
    """To return the number of current window or the number of the window
    `expr`, where `expr` can be # or %. See :h winnr()"""
    if expr is None:
        return int(eval("winnr()"))
    return int(eval(u"winnr('{}')".format(expr)))


def setbuffer(content):
    """To set the whole content of the current buffer at once."""
    enc = encoding()
    if isinstance(content, list):
        vim.current.buffer[:] = [ln.encode(enc) for ln in content]
    elif isinstance(content, basestring):
        vim.current.buffer[:] = content.encode(enc).split("\n")


def getline(linenr):
    """To set a specific line of the current buffer."""
    return vim.current.buffer[linenr].decode(encoding())


def setline(linenr, line):
    """To set a specific line of the current buffer."""
    vim.current.buffer[linenr] = line.encode(encoding())


def setwinh(height):
    """To set the height of the current window."""
    vim.current.window.height = height


def buflisted(expr):
    """To check if a buffer is listed. See :h buflisted()"""
    if isinstance(expr, basestring):
        return call(u"buflisted('{}')".format(expr))
    return call(u"buflisted({})".format(expr))


def buffers():
    """To return a list of all listed buffers."""
    enc = encoding()
    named = ifilter(lambda b: b.name, vim.buffers)
    decoded = imap(lambda b: normalize("NFC", b.name.decode(enc)), named)
    return ifilter(lambda b: buflisted(b), decoded)
