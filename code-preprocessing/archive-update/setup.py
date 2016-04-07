#!/usr/bin/env python
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import setuptools  # Required for Windows
from distutils.core import setup
from distutils.extension import Extension

import numpy as np

from Cython.Distutils import build_ext

extensions = []

print('Using Cython to build interface.')
    
extensions.append(Extension('cocoprep.coco_archive',
                            sources=['interface/coco_archive.pyx', 'interface/coco.c'],
                            include_dirs=[np.get_include()]))

setup(
    name='cocoprep',
    version="0.1",
    packages=['cocoprep'],
    package_dir={'cocoprep': 'python'},
    description='A COCO package for handling archives in pre-processing',
    ext_modules=extensions,
    cmdclass={'build_ext': build_ext}
)
