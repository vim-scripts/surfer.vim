# -*- coding: utf-8 -*-
"""
tests.py
~~~~~~~~

Tests for tsurf.
"""

import unittest

from tsurf.utils import search
from tsurf.ext import search as _search


# tests for the modules 'tsurf.utils.search' and 'tsurf.ext.search'
# ===========================================================================

class TestSearch(unittest.TestCase):

    def setUp(self):

        # dictionary form:
        #    input               expected output
        #   {(needle, haystack): (score: match positions), ..}

        self.search_tests = {
            ("whatever", "") : (-1, tuple()),
            ("whatever", "clusterSendMessage") : (-1, tuple()),
            ("", "clusterSendMessage") : (-1, tuple()),
            ("cls", "clusterSendMessage") : (4, (0,1,3)),
            ("clse", "clusterSendMessage") : (5, (0,1,7,8)),
            ("sde", "clusterSendMessage") : (10, (7,10,12)),
            ("send", "clusterSendMessage") : (1.6667, (7,8,9,10)),
            ("Send", "clusterSendMessage") : (1.6667, (7,8,9,10)),
            ("clsend", "clusterSendMessage") : (5, (0,1,7,8,9,10)),
        }

        self.smart_search_tests = {
            ("", "clusterSendMessage") : (-1, tuple()),
            ("cls", "clusterSendMessage") : (4, (0,1,3)),
            ("clse", "clusterSendMessage") : (5, (0,1,7,8)),
            ("clSe", "clusterSendMessage") : (5, (0,1,7,8)),
            ("clSE", "clusterSendMessage") : (-1, tuple()),
            ("clsM", "clusterSendMessage") : (6.5, (0,1,7,11)),
            ("clSM", "clusterSendMessage") : (6.5, (0,1,7,11)),
            ("clssS", "clusterSendMessage") : (-1, tuple()),
        }

    def test__search(self):
        for (needle, haystack), expected in self.search_tests.items():
            score, positions = search.search(needle, haystack, False)
            self.assertAlmostEqual(score, expected[0], 4)
            self.assertEqual(positions, expected[1])

    def test__search_smart(self):
        for (needle, haystack), expected in self.smart_search_tests.items():
            score, positions = search.search(needle, haystack, True)
            self.assertAlmostEqual(score, expected[0], 4)
            self.assertEqual(positions, expected[1])

    def test__search_ext(self):
        for (needle, haystack), expected in self.search_tests.items():
            score, positions = _search.search(needle, haystack, False)
            self.assertAlmostEqual(score, expected[0], 4)
            self.assertEqual(positions, expected[1])

    def test__search_ext_smart(self):
        for (needle, haystack), expected in self.smart_search_tests.items():
            score, positions = _search.search(needle, haystack, True)
            self.assertAlmostEqual(score, expected[0], 4)
            self.assertEqual(positions, expected[1])


def run():
    unittest.main(module=__name__)
