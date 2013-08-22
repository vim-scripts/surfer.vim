# -*- coding: utf-8 -*-
"""
tsurf.ui
~~~~~~~~

This module defines the UserInterface class. This class is responsible
for showing up the Tag Surfer user interface and to display to the user
all matching tags for the given search query.
"""

import os
import vim
from operator import itemgetter
from collections import namedtuple
from itertools import imap, groupby

from tsurf import exceptions as ex
from tsurf.utils import settings
from tsurf.utils import input
from tsurf.utils import v


class UserInterface:

    def __init__(self, plug):
        self.plug = plug
        self.name = '__om__'

        # This ease passing around current buffer information. We need this
        # because once the finder is open we can no longer access local buffer
        # information since the focus is constantly on the finder window.
        self.CurrBuffer = namedtuple(
            "CurrBuffer", "content name cursor winnr ft")

        # The renderer is responsible for rendering all search results
        # in the finder window
        self.renderer = Renderer(plug)
        self.renderer.setup_colors()

        self._reset()

    def open(self):
        """To open the Tag Surfer user interface."""
        # The Fugitive plugin seems to interfere with Tag Surfer since Fugitive
        # add some filenames to the option `tags`. Tag Surfer does this too,
        # but if Fugitive is installed and the user is editing a file in a git
        # repository, it seems that Tag Surfer cannot append anything to the
        # `tag` option. However, I haven't still figured out why running this
        # seemengly useless command fix the issue. Note that this command works
        # only if called at this location. This surely isn't magic but this is
        # very strange.
        vim.command("exe 'set tags=' . &tags")

        # Save some info about the current buffer
        self.curr_buf = self.CurrBuffer(
            vim.current.buffer,
            vim.current.buffer.name,
            vim.current.window.cursor,
            v.winnr(),
            vim.eval("&ft"))

        # Populate the search results window with tags from the current buffer
        # even though the user haven't searched anything yet.
        self._update()

        # Start the input loop
        key = input.Input()
        while True:

            # Display the prompt and the current search string
            prompt = settings.get("prompt")
            color = settings.get("prompt_color")
            vim.command("echohl {} | echon \"{}\" | echohl None".format(color, prompt))
            query = self.input_so_far.encode('utf-8')
            query = query.replace("\\", "\\\\").replace('"', '\\"')
            vim.command("echon \"{}\"".format(query))

            # Wait for the next key
            key.get()

            if (key.RETURN or key.CTRL and key.CHAR in ('g', 'o', 'p', 's')):
                # Go to the tag on the current line
                prefix = key.CHAR if key.CHAR in ('s', 'p') else ''
                if self._open_selected_tag(prefix):
                    self.plug.finder.rebuild_tags = True
                    self.plug.finder.refind_tags = True
                    break

            elif key.BS:
                # If the search scope changes, rebuild the cache
                pmod = settings.get("project_search_modifier")
                bmod = settings.get("buffer_search_modifier")
                self.plug.finder.refind_tags = True
                if self.input_so_far and self.input_so_far[-1] in (pmod, bmod):
                    self.plug.finder.rebuild_tags = True

                # Delete a character
                self.input_so_far = u"{}".format(self.input_so_far)[:-1]
                self.curr_line_idx = -1

            elif key.ESC or key.INTERRUPT:
                # Close the finder window
                self.close()
                self.plug.finder.rebuild_tags = True
                self.plug.finder.refind_tags = True
                break

            elif key.UP or key.TAB or key.CTRL and key.CHAR == 'k':
                # Move up the cursor
                last_index = len(vim.current.buffer) - 1
                if self.curr_line_idx == 0:
                    self.curr_line_idx = last_index
                else:
                    self.curr_line_idx -= 1

            elif key.DOWN or key.CTRL and key.CHAR == 'j':
                # Move down the cursor
                last_index = len(vim.current.buffer) - 1
                if self.curr_line_idx == last_index:
                    self.curr_line_idx = 0
                else:
                    self.curr_line_idx += 1

            elif key.CTRL and key.CHAR == 'u':
                # Clear the current search
                self.input_so_far = ''
                self.curr_line_idx = -1
                self.plug.finder.refind_tags = True

            elif key.CHAR:
                # A character has been pressed.
                self.input_so_far += key.CHAR
                self.curr_line_idx = -1
                # If the search scope changes, rebuild the cache
                pmod = settings.get("project_search_modifier")
                bmod = settings.get("buffer_search_modifier")
                self.plug.finder.refind_tags = True
                if key.CHAR in (pmod, bmod) or len(self.input_so_far) == 1:
                    self.plug.finder.rebuild_tags = True

            else:
                v.redraw()
                continue

            self._update()

    def close(self):
        """To close the Tag Surfer user interface."""
        self._restore_options()
        vim.command('q')
        if self.curr_buf.winnr:
            v.focus_win(self.curr_buf.winnr)
        self._reset()

    def _reset(self):
        """To reset the Tag Surfer user interface state."""
        self.curr_buf = None
        self.input_so_far = ''
        self.finder_win = None
        self.curr_line_idx = -1  # line index in the finder window
        self.mapper = {}
        self.orig_settings = {}
        self.plug.finder.rebuild_tags = True
        self.plug.finder.refind_tags = True

    def _setup_buffer(self):
        """To set sane options for the search results buffer."""
        # save options that affect all windows and thus cannot be safely set
        # using 'selocal' and we need to manually restore their old values
        self.orig_settings = {
            # It seems that somethimes in gVim `vim.eval('@/')` returns `None`
            "@/": "" if vim.eval("@/") is None else vim.eval("@/"),
            "laststatus": vim.eval("&laststatus"),
            "guicursor": vim.eval("&guicursor"),
            "statusline": vim.eval("&statusline").replace(" ", "\ ")
        }

        vim.command('let @/ = ""')  # clear the last search

        options = [
            "buftype=nofile", "bufhidden=wipe", "encoding=utf-8",
            "nobuflisted", "noundofile", "nobackup", "noswapfile",
            "nowrap", "nonumber", "cursorline", "nolist", "textwidth=0",
            "colorcolumn=0", "laststatus=0", "norelativenumber",
            "guicursor=a:hor5-Cursor-blinkwait100",
            "nocursorcolumn", "nospell"
        ]

        # Show the statusline in debug mode
        if settings.get("debug", bool):
            options.append("laststatus=2")

        for opt in options:
            vim.command("try|setl {}|catch|endtry".format(opt))

    def _restore_options(self):
        """To restore original options."""
        for sett, val in self.orig_settings.items():
            if sett in ("@/",):
                vim.command("let {}=\"{}\" ".format(
                    sett, val.replace('"', '\\"')))
            else:
                vim.command('set {}={}'.format(sett, val))

    def _update(self):
        """To update search results."""
        if not self.finder_win:
            # Open the finder window if not already visible
            vim.command('silent! botright split {}'.format(self.name))
            self._setup_buffer()
            self.finder_win = v.bufwinnr(self.name)

        tags = []
        error = None
        try:
            max_results = settings.get('max_results', int)
            tags = self.plug.finder.find_tags(self.input_so_far, max_results, self.curr_buf)
            self.plug.finder.rebuild_tags = False
            self.plug.finder.refind_tags = False
        except ex.TagSurferException as e:
            error = e

        self.mapper, self.curr_line_idx = self.renderer.render(self.finder_win,
                self.curr_line_idx, self.input_so_far, tags, error)

        v.redraw()

    def _compute_tag_candidates_scores(self, lines, tag):
        """To compute the score for each candidate tag from the output
        of the `:tselect <tag>` command. The higher, the better.

        Run the `:tselect` command to view how its output is structured.

        TODO: check correctness.
        """

        def extract_kind(line):
            last_idx = line.find(tag["name"]) - 1
            first_idx = line[:last_idx+1].rfind(" ") + 1
            return line[first_idx:last_idx]

        def get_tag_line(tag):
            if tag["exts"].get("line") or tag["excmd"].isdigit():
                return tag["exts"].get("line", tag["excmd"])
            else:
                return ""

        candidates = {}
        curr_candidate = -1

        for line in imap(lambda l: l.strip("> \n"), lines):

            if line.startswith("#"):
                continue

            if line and line[0].isdigit() and tag["name"] in line:
                # The line starts with a number, this is the tag count,
                # that is, the number that with can use in conjunction with
                # the `:tag` command to get a specific tag (e.g. `:2tag <tag>`)
                curr_candidate = line[0]
                candidates[curr_candidate] = 0

                if line.split()[-1] == tag["file"]:
                    candidates[curr_candidate] += 1
                if extract_kind(line) == tag["exts"].get("kind"):
                    candidates[curr_candidate] += 1

            else:
                if curr_candidate > 0:
                    found = False
                    for f in line.split():
                        if f.startswith("line:"):
                            if line[6:] == get_tag_line(tag):
                                found = True
                                candidates[curr_candidate] += 1
                    if not found:
                        if line == tag["excmd"][2:-2]:
                            candidates[curr_candidate] += 1

        return candidates

    def _get_best_tag_candidate(self, tag):
        """To get the best tag candidate for a given tag name.

        We do this parsing the output of the `:tselect <tag>`
        vim command.
        """
        tempf = vim.eval("tempname()")
        vim.command("""
            redir > {} |
            try | silent! ts {} | catch | endtry |
            redir END""".format(tempf, tag["name"]))
        lines = vim.eval("readfile('{}')".format(tempf))
        scores = self._compute_tag_candidates_scores(lines, tag)
        try:
            os.remove(tempf)
        except OSError:
            pass

        if scores:
            return max(scores.items(), key=itemgetter(1))[0]

    def _open_selected_tag(self, prefix=""):
        """To open the tag on the current line."""
        tag = self.mapper.get(self.curr_line_idx)
        if tag:
            self.close()

            # There may be more tags with the same name, so we
            # have to pick the best candidate
            count = self._get_best_tag_candidate(tag)
            if count:
                vim.command("silent {}{}tag {}".format(
                    count, prefix, tag["name"]))
            else:
                # An error occurred, probably no tag file has been found
                v.echohl(
                    "No tag file found. be sure that the `tags` option "
                    "is not changed while Tag Surfer is working",
                    "WarningMsg")

            vim.command("normal! zz")  # center the screen
            return True


class Renderer:

    def __init__(self, plug):
        self.plug = plug
        self.last_matches = []

    def setup_colors(self):
        """To setup Tag Surfer highlight groups."""
        postfix = "" if vim.eval("&bg") == "light" else "_darkbg"
        shade = settings.get("shade_color{}".format(postfix))
        matches = settings.get("matches_color{}".format(postfix))

        for g, color in (("Shade", shade), ("Matches", matches)):
            if "=" in color:
                vim.command("hi TagSurfer{} {}".format(g, color))
            else:
                vim.command("hi link TagSurfer{} {}".format(g, color))

        vim.command("hi link TagSurferError WarningMsg")

    def render(self, target_win, curr_line_idx, query, tags, error=None):
        """To render all search results."""
        v.focus_win(target_win)
        vim.command('syntax clear')
        self.last_matches = []
        mapper = {}

        if error:

            v.set_buffer(error.message)
            self._highlight(error=True)
            v.set_win_height(len(error.message.split("\n")))
            curr_line_idx = 0

        elif tags:

            # Find duplicates file names
            dups = {}
            for _, g in groupby(tags, key=lambda t: os.path.basename(t["file"])):
                # s is a set of unique paths but with the same basename
                s = set(t["file"] for t in g)
                if len(s) > 1:
                    dups.update((file, True) for file in s)

            mapper = dict(enumerate(t for t in tags))
            self.last_matches = [t["match_positions"] for t in tags]
            v.set_buffer([self._render_line(t, query, dups) for t in tags])
            curr_line_idx = self._render_curr_line(curr_line_idx)
            self._highlight()
            v.set_win_height(len(tags))

        else:

            v.set_buffer(settings.get("no_results_msg"))
            v.set_win_height(1)
            curr_line_idx = 0

        v.set_win_cursor(curr_line_idx + 1, 0)
        vim.command("normal! 0")

        return mapper, curr_line_idx

    def _render_line(self, tag, query, dups_fnames):
        """To format a single line with the tag information."""

        def fmt_file(tag):
            """Format tag file."""
            pmod = settings.get("project_search_modifier")
            bmod = settings.get("buffer_search_modifier")

            file = tag["file"].encode('utf-8')
            root = self.plug.services.curr_project.get_root()

            if settings.get("tag_file_full_path", bool):
                if query.startswith(pmod) and root:
                    # The search scope is the current projet and the project
                    # root exists
                    f = file.replace(root, "")
                    return f[1:] if f.startswith(os.path.sep) else f
                else:
                    # The search scope is the current projet but there
                    # is no project root
                    return file.replace(os.path.expanduser("~"), "~")

            # The user always wants the tag file displayed relative to the
            # current project root if it exists. Replacing the home with
            # '~' may be needed for files outside the current project that
            # are printed with the absolute path.
            if settings.get("tag_file_relative_to_project_root", bool):
                if root:
                    f = file.replace(root, "").replace(
                            os.path.expanduser("~"), "~")
                    return f[1:] if f.startswith(os.path.sep) else f

            # If the `g:tsurf_tag_file_custom_depth` is set,
            # cut the path according its value
            depth = settings.get("tag_file_custom_depth", int)
            if depth > 0:
                return os.path.join(*file.split(os.path.sep)[-depth:])

            # If th file name is duplicate in among search results
            # then display also the container directory
            if file in dups_fnames and len(file.split(os.path.sep)) > 1:
                return os.path.join(*file.split(os.path.sep)[-2:])

            # By default display only the file name
            return os.path.basename(file)

        def fmt_debug(tag):
            """Format debug information."""
            if settings.get("debug", bool):
                return  " | debug: ({:.4f}|{})".format(
                    tag["similarity"], tag["match_positions"])
            return ""

        def get_linenr(tag):
            """Get line number if available."""
            if tag["exts"].get("line") or tag["excmd"].isdigit():
                return tag["exts"].get("line", tag["excmd"])
            else:
                return ""

        def fmt(fmtstr):
            """Replace the attribute in `fmtdtr` with its value."""
            if "{name}" in fmtstr:
                return fmtstr.replace("{name}", tag["name"])
            if "{excmd}" in fmtstr:
                return fmtstr.replace("{excmd}", tag["excmd"])
            if "{file}" in fmtstr:
                return fmtstr.replace("{file}", fmt_file(tag))
            if "{context}" in fmtstr:
                return fmtstr.replace("{context}", tag["context"])
            if "{line}" in fmtstr:
                ln = get_linenr(tag)
                if ln:
                    return fmtstr.replace("{line}", ln)
                else:
                    return ""
            try:
                return fmtstr.format(**tag["exts"])
            except KeyError:
                return ""

        return "{}{} @ {}{}".format(
            " "*len(settings.get("current_line_indicator")),
            tag["name"].encode('utf-8'),
            "".join(fmt(fmtstr) for fmtstr in settings.get("line_format")),
            fmt_debug(tag))

    def _render_curr_line(self, curr_line_idx):
        """To add an indicator in front of the current line."""
        if curr_line_idx < 0:
            curr_line_idx = len(vim.current.buffer) - 1

        line = vim.current.buffer[curr_line_idx]
        indicator = settings.get("current_line_indicator")
        v.set_buffer_line(curr_line_idx, indicator + line[len(indicator):])

        return curr_line_idx

    def _highlight(self, error=False):
        """To color the Tag Surfer user interface."""
        vim.command("syntax clear")
        if error:
            v.synmatch("TagSurferError", ".*")
        else:
            v.synmatch("TagSurferShade", "@.*")
            indic_len = len(settings.get("current_line_indicator"))
            for i, match_positions in enumerate(self.last_matches):
                for pos in match_positions:
                    patt = "\c\%{}l\%{}c.".format(i+1, pos+indic_len+1)
                    v.synmatch("TagSurferMatches", patt)
