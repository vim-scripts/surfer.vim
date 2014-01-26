#ifndef SEARCHMODULE_H
#define SEARCHMODULE_H

#include <Python.h>
#include <ctype.h>


int _isupper(const Py_UNICODE *c, int);

float _similarity(int, PyObject*, int);


#endif
