#ifndef SEARCHMODULE_H
#define SEARCHMODULE_H

#include <Python.h>
#include <ctype.h>


/*
 * To compute the similarity between two strings given the `haystack` length,
 * and the positions where `needle` matches in `haystack` and the positions
 * where matches fall on word boundaries.
 *
 * Returns a number that indicate the similarity between the two strings.
 * The lower it is, the more similar the two strings are.
 *
 */
float similarity(int, PyObject*, int);

#endif
