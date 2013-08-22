#!/usr/bin/env bash

cd ./autoload/tsurf/ext
python setup.py build_ext --inplace
rm -fR build
