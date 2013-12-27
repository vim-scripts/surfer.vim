# -*- coding: utf-8 -*-
"""
surfer.ui
~~~~~~~~~

This module defines the UserInterface class. This class is responsible
for showing up the Surfer user interface and to display to the user
all matching tags for the given search query.
"""

import os
import vim
from operator import itemgetter
from collections import namedtuple
from itertools import imap, groupby

from surfer.utils import v
from surfer.utils import input
from surfer.utils import settings
from surfer import exceptions as ex


class UserInterface:

    def __init__(self, plug):
        self.plug = plug
        self.name = '__surfer__'
        self.renderer = Renderer(plug)
        self.BufInfo = namedtuple("BufInfo", "name winnr")
        self.setup_colors()
        self._reset()

    def open(self):
        """To open the Surfer user interface."""
        # The Fugitive plugin seems to interfere with Surfer since it adds
        # some filenames to the vim option `tags`. Surfer does this too,
        # but if Fugitive is installed and the user is editing a file in a git
        # repository, it seems that Surfer cannot append anything to the
        # `tag` option. I haven't still figured out why this happens but this
        # seems to fix the issue.
        vim.command("exe 'set tags='.&tags")

        self.user_buf = self.BufInfo(v.bufname(), v.winnr())
        pmod = settings.get("project_search_modifier")
        bmod = settings.get("buffer_search_modifier")

        self._open_window()
        self.renderer.render(self.winnr, -1, "", [], "")
        v.redraw()

        # Start the input loop
        key = input.Input()
        while True:

            self.perform_new_search = True

            # Display the prompt and the current query
            prompt = settings.get("prompt")
            query = self.query.replace("\\", "\\\\").replace('"', '\\"')
            vim.command("echohl SurferPrompt | echon \"{}\" | echohl None".format(prompt))
            vim.command("echon \"{}\"".format(query.encode('utf-8')))

            # Wait for the next pressed key
            key.get()

            # Go to the tag on the current line
            if (key.RETURN or key.CTRL and key.CHAR in ('g', 'o', 'p', 's')):
                mode = key.CHAR if key.CHAR in ('s', 'p') else ''
                tag = self.mapper.get(self.cursor_pos)
                if tag:
                    self._jump_to(tag, mode)
                    break

            # Close the Surfer window
            elif key.ESC or key.INTERRUPT:
                self._close()
                break

            # Delete a character backward
            elif key.BS:
                query = self.query.strip()
                if query and query in (bmod, pmod):
                    self.plug.generator.rebuild_tags = True
                self.query = u"{}".format(self.query)[:-1]
                self.cursor_pos = -1  # move the cursor to the bottom

            # Move the cursor up
            elif key.UP or key.TAB or key.CTRL and key.CHAR == 'k':
                self.perform_new_search = False
                if self.cursor_pos == 0:
                    self.cursor_pos = len(vim.current.buffer) - 1
                else:
                    self.cursor_pos -= 1

            # Move the cursor down
            elif key.DOWN or key.CTRL and key.CHAR == 'j':
                self.perform_new_search = False
                if self.cursor_pos == len(vim.current.buffer) - 1:
                    self.cursor_pos = 0
                else:
                    self.cursor_pos += 1

            # Clear the current search
            elif key.CTRL and key.CHAR == 'u':
                query = self.query.lstrip()
                if query and query[0] in (bmod, pmod):
                        self.query = query[0]
                else:
                    self.query = ""
                self.cursor_pos = -1  # move the cursor to the bottom

            # A character has been pressed.
            elif key.CHAR:
                self.query += key.CHAR
                self.cursor_pos = -1  # move the cursor to the bottom
                if key.CHAR in (pmod, bmod) and len(self.query.strip()) == 1:
                    self.plug.generator.rebuild_tags = True

            else:
                v.redraw()
                continue

            self._update()
            v.redraw()

    def _open_window(self):
        """To open the Surfer window if not already visible."""
        if not self.winnr:
            vim.command('sil! botright split {}'.format(self.name))
            self._setup_buffer()
            self.winnr = v.bufwinnr(self.name)

    def _close(self):
        """To close the Surfer user interface."""
        self._restore_options()
        vim.command('q')
        if self.user_buf.winnr:
            v.focus_win(self.user_buf.winnr)
        self._reset()
        v.redraw()

    def _reset(self):
        """To reset the Surfer user interface state."""
        self.user_buf = None
        self.query = ''
        self.winnr = None
        self.mapper = {}
        self.cursor_pos = -1  # line index in the finder window
        self.orig_settings = {}
        self.search_results_cache = []
        self.perform_new_search = True

    def _setup_buffer(self):
        """To set sane options for the search results buffer."""
        self.orig_settings = {
            # It seems that somethimes in gVim `vim.eval('@/')` returns `None`
            "@/": "" if vim.eval("@/") is None else vim.eval("@/"),
            "laststatus": vim.eval("&laststatus"),
            "guicursor": vim.eval("&guicursor"),
            "statusline": vim.eval("&statusline").replace(" ", "\ ")
        }

        options = [
            "buftype=nofile", "bufhidden=wipe", "encoding=utf-8",
            "nobuflisted", "noundofile", "nobackup", "noswapfile",
            "nowrap", "nonumber", "cursorline", "nolist", "textwidth=0",
            "colorcolumn=0", "laststatus=0", "norelativenumber",
            "guicursor=a:hor5-Cursor-blinkwait100",
            "nocursorcolumn", "nospell"
        ]

        if settings.get("debug", bool):
            options.append("laststatus=2")  # debug

        vim.command('let @/ = ""')  # clear the last search
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

    def setup_colors(self):
        """To setup Surfer highlight groups."""
        postfix = "" if vim.eval("&bg") == "light" else "_darkbg"
        colors = {
            "SurferShade": settings.get("shade_color{}".format(postfix)),
            "SurferMatches": settings.get("matches_color{}".format(postfix)),
            "SurferPrompt": settings.get("prompt_color{}".format(postfix)),
            "SurferError": "WarningMsg"
        }
        for group, color in colors.items():
            if color:
                link = "" if "=" in color else "link"
                vim.command("hi {} {} {}".format(link, group, color))

        colors = settings.get("visual_kinds_colors{}".format(postfix))
        for kind, color in colors.items():
            if color:
                link = "" if "=" in color else "link"
                vim.command("hi {} SurferVisualKind_{} {}".format(link, kind, color))

    def _update(self):
        """To update search results."""
        tags = []
        error = ""
        if self.perform_new_search:
            try:
                max_results = settings.get('max_results', int)
                tags = self.plug.finder.find_tags(
                    self.query, max_results, self.user_buf.name)
                self.search_results_cache = tags
            except ex.SurferException as e:
                error = e.message
        else:
            tags = self.search_results_cache

        self.mapper, self.cursor_pos = self.renderer.render(
                self.winnr, self.cursor_pos, self.query, tags,
                msg=error, iserror=bool(error))

    def _jump_to(self, tag, mode=""):
        """To jump to the tag on the current line."""
        self._close()
        count = self._tag_count(tag)
        vim.command("sil! {}{}tag {}".format(count, mode, tag["name"]))
        vim.command("normal! zvzzg^")

    def _tag_count(self, tag):
        """To pick the best tag candidate for a given tag name.

        The number retruned is meant to be used in conjunction with the :tag
        vim command (see :h :tag)
        """
        candidates = vim.eval('taglist("{}")'.format(tag["name"]))
        if len(candidates) == 1:
            return 1

        #  group tags by file name
        groups = []
        for fname, g in groupby(candidates, key=itemgetter("filename")):
            groups.append((fname, list(g)))
        groups.sort(key=itemgetter(0))

        # sort tags by the `line` field (XXX: or `cmd`?); tags from of the
        # current buffer are put first. This is ensures that the `:[count]tag
        # [name]` command will work as expected (see :h tag-priority)
        ordered_candidates = []
        for fname, tags in groups:
            sorted_tags = sorted(tags, key=itemgetter("line"))
            if fname == v.bufname():
                ordered_candidates = sorted_tags + ordered_candidates
            else:
                ordered_candidates.extend(sorted_tags)

        scores = [0]*len(ordered_candidates)
        for i, candidate in enumerate(ordered_candidates):
            if candidate["cmd"] == tag["cmd"]:
                scores[i] += 1
            if candidate["name"] == tag["name"]:
                scores[i] += 1
            if candidate["filename"] == tag["file"]:
                scores[i] += 1
            if candidate["line"] == tag["exts"].get("line"):
                scores[i] += 1
            if candidate["kind"] == tag["exts"].get("kind"):
                scores[i] += 1
            if candidate["language"] == tag["exts"].get("language"):
                scores[i] += 1

        return scores.index(max(scores)) + 1


class Renderer:

    def __init__(self, plug):
        self.plug = plug
        self.formatter = Formatter(plug)

    def render(self, target_win, cursor_pos, query, tags, msg="", iserror=False):
        """To render all search results."""
        vim.command('syntax clear')
        v.focus_win(target_win)
        mapper = {}

        if not tags and not msg:
            msg = settings.get("no_results_msg")

        if msg:

            v.set_buffer(msg)
            v.set_win_height(len(msg.split("\n")))
            cursor_pos = 0
            if iserror:
                self._highlight_err()

        else:

            # Find duplicates file names
            dups = {}
            for _, g in groupby(tags, key=lambda t: os.path.basename(t["file"])):
                # s is a set of unique paths but with the same basename
                s = set(t["file"] for t in g)
                if len(s) > 1:
                    dups.update((file, True) for file in s)

            tags = tags[::-1]
            mapper = dict(enumerate(t for t in tags))
            v.set_buffer([self._render_line(t, query, dups) for t in tags])
            cursor_pos = self._render_curr_line(cursor_pos)
            self._highlight_tags(tags)
            v.set_win_height(len(tags))

        v.cursor((cursor_pos + 1, 0))
        vim.command("normal! 0")

        return mapper, cursor_pos

    def _render_line(self, tag, query, dups_fnames):
        """To format a single line with the tag information."""
        line_format = settings.get("line_format")
        visual_kind = ""
        if settings.get("visual_kinds", bool):
            visual_kind = settings.get("visual_kinds_shape") + " "

        return "{}{}{}{}{}".format(
            " "*len(settings.get("current_line_indicator")),
            visual_kind,
            tag["name"].encode('utf-8'),
            "".join(self.formatter.fmt(fmtstr, tag, dups_fnames) for fmtstr in line_format),
            self.formatter.fmt_debug(tag))

    def _render_curr_line(self, cursor_pos):
        """To add an indicator in front of the current line."""
        if cursor_pos < 0:
            cursor_pos = len(vim.current.buffer) - 1
        line = vim.current.buffer[cursor_pos]
        indicator = settings.get("current_line_indicator")
        v.set_buffer_line(cursor_pos, indicator + line[len(indicator):])
        return cursor_pos

    def _highlight_err(self):
        """To highlight the content of the Surfer window as error."""
        v.highlight("SurferError", ".*")

    def _highlight_tags(self, tags):
        """To highlight formatted tags."""
        vk_colors = settings.get("visual_kinds_colors")
        vk_shape = settings.get("visual_kinds_shape")

        for i, tag in enumerate(tags):
            for pos in tag["match_positions"]:

                offset = len(settings.get("current_line_indicator"))

                if settings.get("visual_kinds", bool):
                    offset += v.len(vk_shape) + 1
                    kind = tag["exts"].get("kind")
                    if kind in vk_colors:
                        patt = "\c\%{}l{}".format(i+1, vk_shape.replace("\u","\%u"))
                        v.highlight("SurferVisualKind_" + kind, patt)

                patt = "\c\%{}l\%{}c.*".format(i+1, offset+1 + len(tag["name"]))
                v.highlight("SurferShade", patt)

                patt = "\c\%{}l\%{}c.".format(i+1, pos+offset+1)
                v.highlight("SurferMatches", patt)


class Formatter:

    def __init__(self, plug):
        self.plug = plug

    def fmt(self, fmtstr, tag, dups_fnames):
        """Replace the attribute in `fmtdtr` with its value."""
        if "{name}" in fmtstr:
            return fmtstr.replace("{name}", tag["name"])
        if "{cmd}" in fmtstr:
            return fmtstr.replace("{cmd}", tag["cmd"])
        if "{file}" in fmtstr:
            return fmtstr.replace("{file}", self._fmt_file(tag, dups_fnames))
        if "{line}" in fmtstr:
            ln = self._get_linenr(tag)
            if ln:
                return fmtstr.replace("{line}", ln)
            else:
                return ""
        try:
            return fmtstr.format(**tag["exts"])
        except KeyError:
            return ""

    def fmt_debug(self, tag):
        """Format debug information."""
        if settings.get("debug", bool):
            return  " | debug: ({:.4f}|{})".format(
                tag["similarity"], tag["match_positions"])
        return ""

    def _fmt_file(self, tag, dups_fnames):
        """Format tag file."""
        pmod = settings.get("project_search_modifier")
        bmod = settings.get("buffer_search_modifier")

        file = tag["file"].encode('utf-8')
        root = self.plug.services.project.get_root()

        # The user always wants the tag file displayed relative to the
        # current project root if it exists. Replacing the home with
        # '~' may be needed for files outside the current project that
        # are printed with the absolute path.
        if settings.get("tag_file_relative_to_project_root", bool):
            if root:
                f = file.replace(root, "").replace(os.path.expanduser("~"), "~")
                return f[1:] if f.startswith(os.path.sep) else f

        # If the `g:surfer_tag_file_custom_depth` is set,
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

    def _get_linenr(self, tag):
        """Get line number if available."""
        if tag["exts"].get("line") or tag["cmd"].isdigit():
            return tag["exts"].get("line", tag["cmd"])
        else:
            return ""
