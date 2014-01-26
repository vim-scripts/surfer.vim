/*
 * searchmodule.c
 *
 * C module extension for better search performances (faster implementation
 * of the module `surfer.search.search`)
 *
 * NOTE: each time this module is improved, the `version` constant MUST be
 * incremented by 1. The vim variable `latest_extension_version` in the file
 * `../autoload/surfer.vim` MUST be updated as well.
 *
 */

#include "searchmodule.h"

#if PY_MAJOR_VERSION < 3
    #define PyLong_AsLong PyInt_AsLong
#endif


const long version = 2;


static char py_match_doc[] = "To search for `needle` in `haystack`.\n"
    "Returns a tuple of two elements: a number and another tuple."
    "The number is a measure of the similarity between `needle` and "
    "`haystack`, whereas the other tuple contains the positions where "
    "the match occurs in `haystack`.";

static PyObject *
py_match(PyObject *self, PyObject *args)
{
    const Py_UNICODE *needle, *haystack;
    const int needle_len, haystack_len;
    const int smart_case;
    int i, j, k;

    if (!PyArg_ParseTuple(args, "u#u#i",
            &needle, &needle_len, &haystack, &haystack_len, &smart_case))
        return NULL;

    if (needle_len == 0) {
        return Py_BuildValue("(i,())", -1);
    }

    // If `haystack` has only uppercase characters then it makes no sense
    // to treat an uppercase letter as a word-boundary character
    int uppercase_is_word_boundary = !_isupper(haystack, haystack_len);

    // Initialize return values
    PyObject *best_positions = Py_BuildValue("()");
    float best_similarity = -1;

    int cond, cond1, cond2;
    int needle_idx;
    Py_UNICODE c, prev;
    Py_UNICODE *_ch;
    PyObject *ch;
    PyObject *pos;
    PyObject *fork, *matcher, *matchers;
    PyObject *consumed, *positions, *boundaries;
    PyObject *needle_obj = PyUnicode_FromUnicode(needle, needle_len);  // new ref XXX

    // `matchers` keeps track of all possible matches of `needle` in `haystack`
    matchers = PyList_New(1);  // new ref

    // Add the first matcher
    matcher = PyDict_New();  // new ref
    PyDict_SetItemString(matcher, "needle_idx", Py_BuildValue("i", 0));
    PyDict_SetItemString(matcher, "consumed", PyList_New(0));
    PyDict_SetItemString(matcher, "boundaries", PyList_New(0));
    PyDict_SetItemString(matcher, "positions", PyList_New(0));
    PyList_SetItem(matchers, 0, matcher);  // PyList_SetItem don't increment the reference count

    for (i = 0; i < haystack_len; i++) {

        // Create forks

        /*assert(PyList_Check(matchers));*/
        for (j = 0; j < PyList_Size(matchers); j++) {

            // get matchers[j] and its values
            matcher = PyList_GetItem(matchers, j);
            /*assert(PyDict_Check(matcher));*/
            consumed = PyDict_GetItemString(matcher, "consumed");
            /*assert(PyList_Check(consumed));*/
            positions = PyDict_GetItemString(matcher, "positions");
            /*assert(PyList_Check(positions));*/
            boundaries = PyDict_GetItemString(matcher, "boundaries");
            /*assert(PyList_Check(boundaries));*/

            // Check if `haystack[i]` has been matched before by matchers[j].
            // If this is the case we crate a fork of matcher[j].

            int idx = -1;
            for (k = 0; k < PyList_Size(consumed); k++) {
                c = PyUnicode_AsUnicode(PyList_GetItem(consumed, k))[0]; // XXX
                /*assert(PyUnicode_Check(c));*/
                if (Py_UNICODE_TOLOWER(haystack[i]) == c) {
                    idx = k;
                    break;
                }
            }

            if (idx >= 0) {
                PyObject *slice = PySequence_GetSlice(needle_obj, idx, needle_len);  // new ref
                /*assert(PySequence_Check(slice));*/
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
                    PyList_Append(matchers, fork);  // PyList_Append increment the ref counter
                    Py_DECREF(fork);
                }
                Py_DECREF(slice);
            }
        }

        // Update each matcher

        /*assert(PyList_Check(matchers));*/
        for (j = 0; j < PyList_Size(matchers); j++) {

            matcher = PyList_GetItem(matchers, j);  // borrowed ref
            /*assert(PyDict_Check(matcher));*/
            consumed = PyDict_GetItemString(matcher, "consumed");
            /*assert(PyList_Check(consumed));*/
            positions = PyDict_GetItemString(matcher, "positions");
            /*assert(PyList_Check(positions));*/
            boundaries = PyDict_GetItemString(matcher, "boundaries");
            /*assert(PyList_Check(boundaries));*/
            needle_idx = PyLong_AsLong(PyDict_GetItemString(matcher, "needle_idx"));

            if (needle_idx == needle_len)
                continue;

            if (smart_case && Py_UNICODE_ISUPPER(needle[needle_idx]))
                cond = haystack[i] == needle[needle_idx];
            else
                cond = Py_UNICODE_TOLOWER(haystack[i]) == Py_UNICODE_TOLOWER(needle[needle_idx]);

            if (cond) {

                prev = haystack[i-1];
                cond1 = uppercase_is_word_boundary && Py_UNICODE_ISUPPER(prev);
                cond2 = 0;
                if (i > 0)
                    cond2 = prev == (Py_UNICODE)('_') || prev == (Py_UNICODE)('-') || Py_UNICODE_ISSPACE(prev);

                if (i == 0 || cond1 || cond2) {
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

                ch = PyUnicode_FromString(" ");  // new ref
                _ch = PyUnicode_AS_UNICODE(ch);
                _ch[0] = Py_UNICODE_TOLOWER(needle[needle_idx]);
                PyList_Append(consumed, ch);
                Py_DECREF(ch);

                needle_idx++;
                PyDict_SetItemString(matcher, "needle_idx", Py_BuildValue("i", needle_idx));

                if (needle_idx == needle_len) {
                    int boundaries_count = 0;
                    for (k = 0; k < PyList_Size(boundaries); k++) {
                        if (PyLong_AsLong(PyList_GetItem(boundaries, k)))
                            boundaries_count++;
                    }
                    float s = _similarity(haystack_len, positions, boundaries_count);
                    if (best_similarity < 0 || s < best_similarity) {
                        best_similarity = s;
                        Py_DECREF(best_positions);
                        best_positions = PySequence_Tuple(positions);
                    }
                }
            }
        }
    }

    Py_DECREF(needle_obj);
    Py_DECREF(matchers);
    return Py_BuildValue("(f,N)", best_similarity, best_positions);
}


float
_similarity(int haystack_len, PyObject *positions, int boundaries_count)
{
    /*assert(PyList_Check(positions));*/

    Py_ssize_t positions_len = PyList_Size(positions);
    if (positions_len == 0)
        return -1;

    int n = 0;
    float diffs_sum = .0;
    int contiguous_sets = 0;
    int positions_sum = 0;

    // Generate all `positions` combinations for k = 2 and
    // sum the absolute difference computed for each one.
    float x1, x2, prev;
    int i, j;
    for (i = 0; i < positions_len; i++) {

        x1 = PyFloat_AsDouble(PyList_GetItem(positions, i));

        positions_sum += x1;

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

    float gravity = positions_sum/positions_len;
    float compactness = .0;
    if (n > 0)
        compactness = diffs_sum/n;

    return gravity + compactness + contiguous_sets - boundaries_count*2.0;
}


int
_isupper(const Py_UNICODE *c, int len)
{
    int i;
    for (i = 0; i < len; i++) {
        if (Py_UNICODE_ISLOWER(c[i]))
            return 0;
    }
    return 1;
}


/* ================================= INIT ================================== */


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
    PyObject *mod;
    mod = PyModule_Create(&searchmodule);
    PyModule_AddIntConstant(mod, "__version__", version);
    return mod;
}

#else

PyMODINIT_FUNC
initsearch(void) {
    PyObject *mod;
    mod = Py_InitModule("search", searchmethods);
    PyModule_AddIntConstant(mod, "__version__", version);
}

#endif
