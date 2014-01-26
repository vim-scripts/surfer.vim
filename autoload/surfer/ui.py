# -*- coding: utf-8 -*-
"""
surfer.ui
~~~~~~~~~

This module defines the UserInterface class. This class is responsible
for showing up the Surfer user interface and to display to the user
all matching tags for the given search query.
"""

import os
from itertools import groupby
from operator import itemgetter
from collections import namedtuple

from surfer.utils import v
from surfer.utils import misc
from surfer.utils import input
from surfer.utils import settings
from surfer import exceptions as ex


class UserInterface:

    def __init__(self, plug):
        self.plug = plug
        self.name = '__surfer__'
        self.renderer = Renderer(plug)
        self.BufInfo = namedtuple("BufInfo", "name nr winnr")
        self.setup_colors()
        self._reset()

    def setup_colors(self):
        """To setup Surfer highlight groups."""
        postfix = "" if v.opt("bg") == "light" else "_darkbg"
        colors = {
            "SurferShade": settings.get("shade_color{}".format(postfix)),
            "SurferMatches": settings.get("matches_color{}".format(postfix)),
            "SurferPrompt": settings.get("prompt_color{}".format(postfix)),
            "SurferError": "WarningMsg"
        }
        for group, color in colors.items():
            if color:
                link = "" if "=" in color else "link"
                v.exe(u"hi {} {} {}".format(link, group, color))

        colors = settings.get("visual_kinds_colors{}".format(postfix))
        for kind, color in colors.items():
            if color:
                link = "" if "=" in color else "link"
                v.exe(u"hi {} SurferVisualKind_{} {}".format(link, kind, color))

    def open(self):
        """To open the Surfer user interface."""
        # The Fugitive plugin seems to interfere with Surfer since it adds
        # some filenames to the vim option `tags`. Surfer does this too,
        # but if Fugitive is installed and the user is editing a file in a git
        # repository, it seems that Surfer cannot append anything to the
        # `tag` option. I haven't still figured out why this happens but this
        # seems to fix the issue.
        v.exe("exe 'set tags='.&tags")

        self.user_buf = self.BufInfo(v.bufname(), v.bufnr(), v.winnr())
        pmod = settings.get("project_search_modifier")
        bmod = settings.get("buffer_search_modifier")

        prompt = u"echohl SurferPrompt | echon \"{}\" | echohl None".format(
            settings.get("prompt"))

        self._open_window()
        self.renderer.render(self.winnr, -1, "", [], "")
        v.redraw()

        # Start the input loop
        key = input.Input()
        while True:

            self.perform_new_search = True

            # Display the prompt and the current query
            v.exe(prompt)
            query = self.query.replace("\\", "\\\\").replace('"', '\\"')
            v.exe(u"echon \"{}\"".format(query))

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
                    self.cursor_pos = len(v.buffer()) - 1
                else:
                    self.cursor_pos -= 1

            # Move the cursor down
            elif key.DOWN or key.CTRL and key.CHAR == 'j':
                self.perform_new_search = False
                if self.cursor_pos == len(v.buffer()) - 1:
                    self.cursor_pos = 0
                else:
                    self.cursor_pos += 1

            # Clear the current search
            elif key.CTRL and key.CHAR == 'u':
                query = self.query.lstrip()
                if query and query[0] in (bmod, pmod):
                        self.query = query[0]
                else:
                    self.query = u""
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
            self.exit_cmds.append(u"set ei={}".format(v.opt("ei")))
            v.exe(u"set eventignore=all")
            v.exe(u'sil! keepa botright 1new {}'.format(self.name))
            self._setup_buffer()
            self.winnr = v.bufwinnr(self.name)

    def _close(self):
        """To close the Surfer user interface."""
        v.exe('q')
        for cmd in self.exit_cmds:
            v.exe(cmd)
        if self.user_buf.winnr:
            v.focus_win(self.user_buf.winnr)
        self._reset()
        v.redraw()

    def _reset(self):
        """To reset the Surfer user interface state."""
        self.user_buf = None
        self.query = u""
        self.winnr = None
        self.mapper = {}
        self.cursor_pos = -1  # line index in the finder window
        self.exit_cmds = []
        self.search_results_cache = []
        self.perform_new_search = True

    def _setup_buffer(self):
        """To set sane options for the search results buffer."""
        last_search = ""
        if v.eval("@/"):
            last_search = v.eval("@/").decode(v.encoding()).replace(u'"', u'\\"')
        self.exit_cmds.extend([
            u"let @/=\"{}\"".format(last_search),
            u"set laststatus={}".format(v.opt("ls")),
            u"set guicursor={}".format(v.opt("gcr")),
        ])

        commands = [
            "let @/ = ''",
            "call clearmatches()"
        ]

        options = [
            "buftype=nofile", "bufhidden=wipe", "nobuflisted", "noundofile",
            "nobackup", "noswapfile", "nowrap", "nonumber", "nolist",
            "textwidth=0", "colorcolumn=0", "laststatus=0", "norelativenumber",
            "nocursorcolumn", "nospell", "foldcolumn=0", "foldcolumn=0",
            "guicursor=a:hor5-Cursor-blinkwait100",
        ]

        if settings.get("cursorline", bool):
            options.append("cursorline")
        else:
            options.append("nocursorline")

        for opt in options:
            v.exe("try|setl {}|catch|endtry".format(opt))

        for cmd in commands:
            v.exe(cmd)

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
        hidden = v.opt("hidden")
        autowriteall = v.opt("autowriteall")
        modified = v.call(u"getbufvar({},'&mod')".format(self.user_buf.nr))
        bufname = self.user_buf.name
        self._close()
        count, tagfile = self._tag_count(tag)
        if (not hidden and not autowriteall) and modified and tagfile != bufname:
            v.echohl(u"write the buffer first. (:h hidden)", "WarningMsg")
        else:
            v.exe(u"sil! {}{}tag {}".format(count, mode, tag["name"]))
            v.exe("normal! zvzzg^")

    def _tag_count(self, tag):
        """To pick the best tag candidate for a given tag name.

        The number retruned is meant to be used in conjunction with the :tag
        vim command (see :h :tag)
        """
        enc = v.encoding()
        candidates = v.call(u'taglist("{}")'.format(tag["name"]))
        if len(candidates) == 1:
            return 1, candidates[0]["filename"].decode(enc)

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
            if fname.decode(enc) == v.bufname():
                ordered_candidates = sorted_tags + ordered_candidates
            else:
                ordered_candidates.extend(sorted_tags)

        files = [c["filename"].decode(enc) for c in ordered_candidates]
        scores = [0]*len(ordered_candidates)
        for i, candidate in enumerate(ordered_candidates):
            if candidate["cmd"].decode(enc) == tag["cmd"]:
                scores[i] += 1
            if candidate["name"].decode(enc) == tag["name"]:
                scores[i] += 1
            if candidate["filename"].decode(enc) == tag["file"]:
                scores[i] += 1
            if candidate["line"].decode(enc) == tag["exts"].get("line"):
                scores[i] += 1
            if candidate["kind"].decode(enc) == tag["exts"].get("kind"):
                scores[i] += 1
            if candidate["language"].decode(enc) == tag["exts"].get("language"):
                scores[i] += 1

        idx = scores.index(max(scores))
        return idx + 1, files[idx]


class Renderer:

    def __init__(self, plug):
        self.plug = plug
        self.formatter = Formatter(plug)

    def render(self, target_win, cursor_pos, query, tags, msg="", iserror=False):
        """To render all search results."""
        v.exe('syntax clear')
        v.focus_win(target_win)
        mapper = {}

        if not tags and not msg:
            msg = settings.get("no_results_msg")

        if msg:

            v.setbuffer(msg)
            v.setwinh(len(msg.split("\n")))
            (len(msg.split("\n")))
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
            v.setbuffer([self._render_line(t, query, dups) for t in tags])
            cursor_pos = self._render_curr_line(cursor_pos)
            self._highlight_tags(tags, cursor_pos)
            v.setwinh(len(tags))

        v.cursor((cursor_pos + 1, 0))
        v.exe("normal! 0")

        return mapper, cursor_pos

    def _render_line(self, tag, query, dups_fnames):
        """To format a single line with the tag information."""
        visual_kind = u""
        if settings.get("visual_kinds", bool):
            visual_kind = settings.get("visual_kinds_shape")
        debug = settings.get("debug", int)
        line_format = settings.get("line_format")
        return u"{}{}{}{}{}".format(
            u" "*len(settings.get("current_line_indicator")),
            visual_kind, tag["name"],
            u"".join(self.formatter.fmt(fmtstr, tag, dups_fnames) for fmtstr in line_format),
            u" [{}]".format(tag["similarity"]) if debug else "")

    def _render_curr_line(self, cursor_pos):
        """To add an indicator in front of the current line."""
        if cursor_pos < 0:
            cursor_pos = len(v.buffer()) - 1

        line = v.getline(cursor_pos)
        indicator = settings.get("current_line_indicator")
        v.setline(cursor_pos, indicator + line[len(indicator):])

        return cursor_pos

    def _highlight_err(self):
        """To highlight the content of the Surfer window as error."""
        v.highlight("SurferError", ".*")

    def _highlight_tags(self, tags, curr_line):
        """To highlight search results."""
        vk_colors = settings.get("visual_kinds_colors")
        vk_shape = settings.get("visual_kinds_shape")
        indicator = settings.get("current_line_indicator")

        for i, tag in enumerate(tags):

            if i == curr_line:
                offset = len(indicator.encode(v.encoding()))
            else:
                offset = len(indicator)

            if settings.get("visual_kinds", bool):
                offset += len(vk_shape.encode(v.encoding()))
                kind = tag["exts"].get("kind")
                if kind in vk_colors:
                    patt = u"\c\%{}l{}".format(i+1, vk_shape.replace(u"u",u"%u"))
                    v.highlight("SurferVisualKind_" + kind, patt)

            patt = u"\c\%{}l\%{}c.*".format(i+1, offset+len(tag["name"])+1)
            v.highlight("SurferShade", patt)

            for pos in misc.as_byte_indexes(tag["match_positions"], tag["name"]):

                patt = u"\c\%{}l\%{}c.".format(i+1, offset+pos+1)
                v.highlight("SurferMatches", patt)


class Formatter:

    def __init__(self, plug):
        self.plug = plug

    def fmt(self, fmtstr, tag, dups_fnames):
        """Replace the attribute in `fmtdtr` with its value."""
        if u"{name}" in fmtstr:
            return fmtstr.replace(u"{name}", tag["name"])
        if u"{cmd}" in fmtstr:
            return fmtstr.replace(u"{cmd}", tag["cmd"])
        if u"{file}" in fmtstr:
            return fmtstr.replace(u"{file}", self._fmt_file(tag, dups_fnames))
        if u"{line}" in fmtstr:
            ln = self._get_linenr(tag)
            if ln:
                return fmtstr.replace(u"{line}", ln)
            else:
                return u""
        try:
            return fmtstr.format(**tag["exts"])
        except KeyError:
            return u""

    def _fmt_file(self, tag, dups_fnames):
        """Format tag file."""
        pmod = settings.get("project_search_modifier")
        bmod = settings.get("buffer_search_modifier")

        file = tag["file"]
        root = self.plug.project.get_root()

        # The user always wants the tag file displayed relative to the
        # current project root if it exists. Replacing the home with
        # '~' may be needed for files outside the current project that
        # are printed with the absolute path.
        if settings.get("tag_file_relative_to_project_root", bool):
            if root:
                f = file.replace(root, u"").replace(os.path.expanduser("~"), u"~")
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
            return u""
