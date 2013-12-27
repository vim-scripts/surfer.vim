# -*- coding: utf-8 -*-
"""
surfer.generator
~~~~~~~~~~~~~~~~

This module defines the TagsGenerator class. This class is responsible for
generating tags.
"""

import os
import vim
import shlex
import tempfile
import subprocess
from os.path import splitext
from fnmatch import fnmatchcase
from itertools import imap, ifilter
from collections import defaultdict

from surfer.utils import v
from surfer.utils import misc
from surfer.utils import settings
from surfer import exceptions as ex


class TagsGenerator:

    def __init__(self, plug):
        self.plug = plug
        self.tags_cache = []
        self.rebuild_tags = True
        self.old_tagfiles = []

    def close(self):
        """To perform cleanup actions."""
        self._remove_tagfiles()

    def get_tags(self, modifier, curr_bufname):
        """To return tags according to the current search scope."""
        if self.rebuild_tags:
            files = self._files(modifier, curr_bufname)
            self.tags_cache = self._build_tags(files)
            self.rebuild_tags = False
        return self.tags_cache

    def _build_tags(self, files):
        """To generate tags for the given `files`.

        If a filetype isn't supported by Exuberant Ctags, then use the custom
        ctags executable provided via the `surfer_custom_languages` option.
        """
        self._remove_tagfiles()

        tags = []
        groups = self._group_files_by_filetype(files)
        for filetype, files in groups.items():

            prg, args, kinds_map, exclude_kinds = self._filetype_data(filetype)
            if not os.path.exists(prg):
                raise ex.SurferException(
                    "Error: The program '{}' does not exists or cannot be "
                    "found in your $PATH".format(prg))

            out, err = self._build(prg, args, files)
            if err and "Warning" not in err:
                raise ex.SurferException(
                    "Error: '{}' failed to generate tags.\nCheck that it's an "
                    "Exuberant Ctags compatible program or that the arguments "
                    "provided are valid".format(prg))

            fn = lambda tag: tag["exts"].get("kind") not in exclude_kinds
            tags.extend(ifilter(fn, self._parse_ctags_output(out, kinds_map)))

        return tags

    def _build(self, prg, args, files):
        """To generate tags."""
        files = imap(lambda f: '"{}"'.format(f), files)
        cmd = "{} {} {}".format(prg, args, " ".join(files))
        cmd = cmd if os.name != 'nt' else cmd.replace("\\", "\\\\")
        startupinfo = None
        if os.name == 'nt':
            # On MS Windows hide the console window when launching a subprocess
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        try:
            ctags = subprocess.Popen(shlex.split(cmd), universal_newlines=True,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    startupinfo=startupinfo)
            return ctags.communicate()
        except Exception as e:
            raise ex.SurferException("Unexpected error: {}".format(e))

    def _parse_ctags_output(self, output, kinds_map):
        """To Parse the ctags output, rebuild the cache and towrite a copy of
        the output to a temporary file.

        Why writing a copy of the output to a temporary file? We do this
        because the temporary file name is appendend to the `tags` vim
        option (set tags+=tempfile) so that the user can still use vim
        commands for navigating tags (<C-T>, etc).
        """
        tagfile = self._generate_tagfile()
        with tagfile:
            for line in output.split("\n"):
                tagfile.write(line + "\n")
                tag = self._parse_tag_line(line, kinds_map)
                if tag:
                    yield tag

    def _parse_tag_line(self, line, kinds_map):
        """To parse a line from a tag file.

        Valid tag line format:

            tagName<TAB>tagFile<TAB>exCmd;"<TAB>extensions

        Where `extensions` is a list of <TAB>-separated fields that can be:

            1) a single letter
            2) a string `attribute:value`

        If the fields is a single letter, then the fields is interpreted as
        the kind attribute.

        NOTE: `kinds_map` is a dictionary of the form:

            {"shortKindName": "longKindName", ...}
        """
        try:
            fields, rawexts = line.strip(" \n").split(';"', 1)
            name, file, cmd = (f.decode("utf-8") for f in fields.split("\t"))
            exts = {}
            for ext in rawexts.strip("\t").split("\t"):
                if (len(ext) == 1 and ext.isalpha()) or ":" not in ext:
                    exts["kind"] = kinds_map.get(ext, ext).decode("utf-8")
                else:
                    t, val = ext.split(":", 1)
                    exts[t] = val.decode("utf-8")
            return {'name': name, 'file': file, 'cmd': cmd, 'exts': exts}
        except ValueError:
            return

    def _files(self, modifier, curr_bufname):
        """To return all files for which tags need to be generated."""
        if curr_bufname and modifier == settings.get("buffer_search_modifier"):
            files = [curr_bufname]
        elif modifier == settings.get("project_search_modifier"):
            files = self.plug.services.project.get_files()
        else:
            files = v.buffers()
        exclude = settings.get("exclude")
        fn = lambda path: not any(fnmatchcase(path, patt) for patt in exclude)
        return filter(fn, files)

    def _filetype_data(self, filetype):
        """To return filetype-specific data."""
        if filetype == "*":
            prg = settings.get("ctags_prg")
            args = settings.get("ctags_args")
            kinds_map = {}
            exclude_kinds = settings.get("exclude_kinds")
        else:
            user_langs = settings.get("custom_languages")
            prg = user_langs[filetype].get("ctags_prg", "")
            args = user_langs[filetype].get("ctags_args", "")
            kinds_map = user_langs[filetype].get("kinds_map", {})
            exclude_kinds = user_langs[filetype].get("exclude_kinds", [])

        return prg, args, kinds_map, exclude_kinds

    def _group_files_by_filetype(self, files):
        """To group files by filetype.

        The filetype "*" groups all files that will be parsed with
        `surfer_ctags_prg`.
        """
        user_langs = settings.get("custom_languages")
        extensions_map = {}
        for filetype, values in user_langs.items():
            for extension in values.get("extensions", []):
                extensions_map[extension] = filetype

        groups = defaultdict(list)
        for f in files:
            extension = splitext(f)[1]
            groups[extensions_map.get(extension, "*")].append(f)

        return groups

    def _generate_tagfile(self):
        """To generate a new temporary tagfile and update the vim
        `tags` option."""
        tagfile = tempfile.NamedTemporaryFile(delete=False)
        vim.command("set tags+={}".format(tagfile.name))
        self.old_tagfiles.append(tagfile.name)
        return tagfile

    def _remove_tagfiles(self):
        """To delete all previously created tagfiles."""
        for tagfile in self.old_tagfiles:
            vim.command("set tags-={}".format(tagfile))
            try:
                os.remove(tagfile)
            except OSError:
                pass
