# -*- coding: utf-8 -*-
"""
tsurf.utils.search
~~~~~~~~~~~~~~~~~~

This module defines the search function used by the Finder class
for searching tags that match the user search query.
"""

from __future__ import division


def search(needle, haystack, smart_case):
    """To search for `needle` in `haystack`.

    Returns a tuple of two elements: a number and another tuple.
    The number is a measure of the similarity between `needle` and `haystack`,
    whereas the other tuple contains the positions where the match occurs in
    `haystack`.

    If there are multiple matches, the one with the highest similarity
    (lowest value) is returned.
    """
    if not needle:
        return -1, tuple()

    # If `haystack` has only uppercase characters then it makes no sense
    # to treat an uppercase letter as a word-boundary character
    uppercase_is_word_boundary = True
    if haystack.isupper():
        uppercase_is_word_boundary = False

    # `matchers` keep track of all possible matches of `needle`
    # along `haystack`
    matchers = [{
        "needle_idx": 0,
        # the following list (or strings) have the same length (always)
        "positions": [],  # e.g. [1,2,3,4,..]
        "consumed": "",
        "boundaries": [],  # e.g. [True,False,False,True,...]
    }]

    best_positions = tuple()
    best_similarity = -1

    needle_len = len(needle)
    haystack_len = len(haystack)

    for i, c in enumerate(haystack):

        forks = []
        for matcher in matchers:
            idx = matcher["consumed"].find(c.lower())
            if idx >= 0 and len(needle[idx:]) <= haystack_len - i:
                forks.append({
                    "needle_idx": idx,
                    "consumed": matcher["consumed"][:idx],
                    "positions": matcher["positions"][:idx],
                    "boundaries": matcher["boundaries"][:idx],
                })

        matchers.extend(forks)

        for matcher in matchers:

            if matcher["needle_idx"] == needle_len:
                continue

            if smart_case and needle[matcher["needle_idx"]].isupper():
                cond = c == needle[matcher["needle_idx"]]
            else:
                cond = c.lower() == needle[matcher["needle_idx"]].lower()

            if cond:

                if (i == 0 or (uppercase_is_word_boundary and c.isupper()) or
                    (i > 0 and haystack[i-1] in ('-', '_'))):
                    matcher["boundaries"].append(True)
                else:
                    matcher["boundaries"].append(False)

                matcher["consumed"] += needle[matcher["needle_idx"]].lower()
                matcher["positions"].append(i)
                matcher["needle_idx"] += 1

                if matcher["needle_idx"] == needle_len:

                    s = similarity(haystack_len, matcher["positions"],
                            len(filter(None, matcher["boundaries"])))

                    if best_similarity < 0 or s < best_similarity:
                        best_similarity = s
                        best_positions = tuple(matcher["positions"])

    return best_similarity, best_positions


def similarity(haystack_len, positions, boundaries_count):
    """ To compute the similarity between two strings given `haystack` and the
    positions where `needle` matches in `haystack`.

    Returns a number that indicate the similarity between the two strings.
    The lower it is, the more similar the two strings are.
    """
    if not positions:
        return -1

    n = 0
    diffs_sum = 0
    contiguous_sets = 0

    # Generate all `positions` combinations for k = 2
    positions_len = len(positions)
    for i in range(positions_len):

        if i > 0 and positions[i-1] != positions[i] - 1:
            contiguous_sets += 1

        for j in range(i, positions_len):
            if i != j:
                diffs_sum += abs(positions[i]-positions[j])
                n += 1

    if n > 0:
        return diffs_sum/n * (contiguous_sets + 1) / (boundaries_count + 1)
    else:
        # This branch is executed when len(positions) == 1
        return positions[0] / (boundaries_count + 1)
