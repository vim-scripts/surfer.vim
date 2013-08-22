from distutils.core import setup, Extension

setup(
    ext_modules = [
        Extension('search', sources = ['searchmodule.c'])
    ]
)
