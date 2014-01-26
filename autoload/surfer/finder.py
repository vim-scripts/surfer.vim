# -*- coding: utf-8 -*-
"""
surfer.finder
~~~~~~~~~~~~~

This module defines the TagsFinder class. This class is responsible for
searching tags.
"""

from operator import itemgetter

from surfer.utils import settings

try:
    from surfer.ext.search import match
    SURFER_SEARCH_EXT_LOADED = True
except ImportError:
    from surfer.search.search import match
    SURFER_SEARCH_EXT_LOADED = False


class TagsFinder:

    def __init__(self, plug, generator):
        self.plug = plug
        self.generator = generator

    def find_tags(self, query, max_results=-1, curr_buf=""):
        """To find all matching tags for the given `query`."""
        modifier, query = self._split_query(query.strip())
        if query:
            tags = self.generator.get_tags(modifier, curr_buf)
            return self._find(query, tags, max_results)
        return []

    def _find(self, query, tags, max_results):
        """To find all matching tags for the given `query`."""
        matches = []
        smart_case = settings.get("smart_case", int)

        for tag in tags:
            similarity, positions = match(query, tag["name"], smart_case)
            if positions:
                matches.append({
                    "match_positions": positions,
                    "similarity": similarity,
                    "name": tag["name"],
                    "file": tag["file"],
                    "cmd": tag["cmd"],
                    "exts": tag["exts"]
                })

        l = len(matches)
        if max_results < 0 or max_results > l:
            max_results = l

        return sorted(matches, key=itemgetter("similarity"))[:max_results]

    def _split_query(self, query):
        """To extract the search modifier from the query. The clean query is
        also returned."""
        bmod = settings.get("buffer_search_modifier")
        pmod = settings.get("project_search_modifier")
        if query and query[0] in (pmod, bmod):
            return query[0], query[1:]
        return u"", query
