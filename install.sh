#!/usr/bin/env bash

cd ./autoload/surfer/ext
rm -fR build search.so
python setup.py build_ext --inplace
rm -fR build
