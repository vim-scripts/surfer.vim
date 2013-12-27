/*
 * searchmodule.c
 *
 * C port of the module `surfer.search.search`.
 *
 */

#include "searchmodule.h"

#if PY_MAJOR_VERSION < 3
    #define PyLong_AsLong PyInt_AsLong
#endif


static char py_match_doc[] = "To search for `needle` in `haystack`.\n"
    "Returns a tuple of two elements: a number and another tuple."
    "The number is a measure of the similarity between `needle` and "
    "`haystack`, whereas the other tuple contains the positions where "
    "the match occurs in `haystack`.";

static PyObject *
py_match(PyObject *self, PyObject *args)
{
    const char *needle;
    const int needle_len;
    const char *haystack;
    const int haystack_len;
    const int smart_case;
    int i, j, k;

    if (!PyArg_ParseTuple(args, "s#s#i",
            &needle, &needle_len, &haystack, &haystack_len, &smart_case))
        return NULL;

    if (needle_len == 0) {
        return Py_BuildValue("(i,())", -1);
    }

    // If `haystack` has only uppercase characters then it makes no sense
    // to treat an uppercase letter as a word-boundary character
    int uppercase_is_word_boundary = 0;
    for (i = 0; i < haystack_len; i++) {
        if (haystack[i] >= 97 && haystack[i] <= 122)
            // non-uppercase letter is found
            uppercase_is_word_boundary = 1;
    }

    // Initialize the return values
    PyObject *best_positions = Py_BuildValue("()");
    float best_similarity = -1;

    // Utilities variables
    PyObject *needle_pyobj = Py_BuildValue("s", needle);  // new ref
    Py_ssize_t needle_pyobj_len = PySequence_Length(needle_pyobj);

    // Declarations
    PyObject *matcher, *fork;
    PyObject *consumed, *positions, *boundaries;
    int needle_idx;

    // `matchers` keeps track of all possible matches of `needle` in `haystack`
    PyObject *matchers = PyList_New(1);  // new ref

    // Add the first matcher
    matcher = PyDict_New();  // new ref
    PyDict_SetItemString(matcher, "needle_idx", Py_BuildValue("i", 0));
    PyDict_SetItemString(matcher, "consumed", PyList_New(0));
    PyDict_SetItemString(matcher, "boundaries", PyList_New(0));
    PyDict_SetItemString(matcher, "positions", PyList_New(0));
    // Note: PyList_SetItem don't increment the reference count
    PyList_SetItem(matchers, 0, matcher);

    for (i = 0; i < haystack_len; i++) {

        // create forks of current matches if needed

        Py_ssize_t matchers_len = PyList_Size(matchers);
        for (j = 0; j < matchers_len; j++) {

            // get matchers[j] and its values
            matcher = PyList_GetItem(matchers, j);
            /*assert(PyDict_Check(matcher));*/
            consumed = PyDict_GetItemString(matcher, "consumed");
            /*assert(PyList_Check(consumed));*/
            positions = PyDict_GetItemString(matcher, "positions");
            /*assert(PyList_Check(positions));*/
            boundaries = PyDict_GetItemString(matcher, "boundaries");
            /*assert(PyList_Check(boundaries));*/

            // Check if the current character in `haystack` has been matched
            // before by matchers[j]. If so, we crate a fork of matcher[j].
            int c;
            int idx = -1;
            for (k = 0; k < PyList_Size(consumed); k++) {
                c = PyLong_AsLong(PyList_GetItem(consumed, k));
                if (tolower(haystack[i]) == c) {
                    idx = k;
                    break;
                }
            }
            if (idx >= 0) {
                PyObject *slice = PySequence_GetSlice(needle_pyobj, idx, needle_pyobj_len);  // new ref
                // The slice contains all characters that remains to be matched
                // by this possible fork in `haystack`. If there is room for
                // this remaining characters to be matched in `haystack` then
                // we create a fork, otherwise there is no need to since the
                // match won't certainly succeed.
                if (PySequence_Length(slice) <= haystack_len - i) {
                    // create a new fork
                    fork = PyDict_New();  // new ref
                    PyDict_SetItemString(fork, "needle_idx", Py_BuildValue("i", idx));
                    PyDict_SetItemString(fork, "consumed", PySequence_GetSlice(consumed, 0, idx));
                    PyDict_SetItemString(fork, "boundaries", PySequence_GetSlice(boundaries, 0, idx));
                    PyDict_SetItemString(fork, "positions", PySequence_GetSlice(positions, 0, idx));
                    // append the new fork to matchers pool
                    PyList_Append(matchers, fork);  // PyList_append increment the ref counter
                    Py_DECREF(fork);
                }
                Py_DECREF(slice);
            }
        }

        // update each matcher

        int cond;
        PyObject *pos, *c;

        for (j = 0; j < PyList_Size(matchers); j++) {

            matcher = PyList_GetItem(matchers, j);  // borrowed ref
            /*assert(PyDict_Check(matcher));*/
            needle_idx = PyLong_AsLong(PyDict_GetItemString(matcher, "needle_idx"));
            consumed = PyDict_GetItemString(matcher, "consumed");
            /*assert(PyList_Check(consumed));*/
            positions = PyDict_GetItemString(matcher, "positions");
            /*assert(PyList_Check(positions));*/
            boundaries = PyDict_GetItemString(matcher, "boundaries");
            /*assert(PyList_Check(boundaries));*/

            if (needle_idx == needle_len)
                continue;

            if (smart_case && isupper(needle[needle_idx]))
                cond = haystack[i] == needle[needle_idx];
            else
                cond = tolower(haystack[i]) == tolower(needle[needle_idx]);

            if (cond) {

                if ((uppercase_is_word_boundary && isupper(haystack[i])) || i == 0 ||
                    (i > 0 && (haystack[i-1] == '-' || haystack[i-1] == '_'))) {
                    pos = Py_BuildValue("i", 1);  // new ref
                    PyList_Append(boundaries, pos);
                } else {
                    pos = Py_BuildValue("i", 0);  // new ref
                    PyList_Append(boundaries, pos);
                }
                Py_DECREF(pos);

                pos = Py_BuildValue("i", i);  // new ref
                PyList_Append(positions, pos);
                Py_DECREF(pos);

                c = Py_BuildValue("i", tolower(needle[needle_idx]));  // new ref
                PyList_Append(consumed, c);
                Py_DECREF(c);

                needle_idx++;
                PyDict_SetItemString(matcher, "needle_idx", Py_BuildValue("i", needle_idx));

                if (needle_idx == needle_len) {
                    int boundaries_count = 0;
                    for (k = 0; k < PyList_Size(boundaries); k++) {
                        if (PyLong_AsLong(PyList_GetItem(boundaries, k)))
                            boundaries_count++;
                    }
                    float s = similarity(haystack_len, positions, boundaries_count);
                    if (best_similarity < 0 || s < best_similarity) {
                        best_similarity = s;
                        Py_DECREF(best_positions);  // TODO: correct right ??
                        best_positions = PySequence_Tuple(positions);
                    }
                }
            }
        }
    }
    Py_DECREF(needle_pyobj);
    Py_DECREF(matchers);
    return Py_BuildValue("(f,N)", best_similarity, best_positions);
}


float
similarity(int haystack_len, PyObject *positions, int boundaries_count)
{
    /*assert(PyList_Check(positions));*/

    Py_ssize_t positions_len = PyList_Size(positions);
    if (positions_len == 0)
        return -1;

    int n = 0;
    float diffs_sum = .0;
    int contiguous_sets = 0;

    // Generate all `positions` combinations for k = 2 and
    // sum the absolute difference computed for each one.
    float x1, x2, prev;
    int i, j;
    for (i = 0; i < positions_len; i++) {

        x1 = PyFloat_AsDouble(PyList_GetItem(positions, i));

        if (i > 0) {
            prev = PyFloat_AsDouble(PyList_GetItem(positions, i-1));
            if (prev != x1 - 1)
                contiguous_sets++;
        }

        for (j = i; j < positions_len; j++) {
            if (j != i) {
                x2 = PyFloat_AsDouble(PyList_GetItem(positions, j));
                diffs_sum += abs(x1-x2);
                n += 1;
            }
        }
    }

    float first_pos = PyFloat_AsDouble(PyList_GetItem(positions, 0));
    float compactness = .0;

    if (n > 0)
        compactness = diffs_sum/n;

    return first_pos + compactness + contiguous_sets - boundaries_count + 1;
}

static PyMethodDef searchmethods[] = {
    {"match", py_match, METH_VARARGS, py_match_doc},
    {NULL, NULL, 0, NULL}
};

#if PY_MAJOR_VERSION >= 3

static struct PyModuleDef searchmodule = {
    PyModuleDef_HEAD_INIT,
    "search",
    NULL,
    -1,
    searchmethods
};

PyMODINIT_FUNC
PyInit_search(void) {
    return PyModule_Create(&searchmodule);
}

#else

PyMODINIT_FUNC
initsearch(void) {
    Py_InitModule("search", searchmethods);
}

#endif
