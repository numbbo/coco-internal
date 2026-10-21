"""Build cocoprep.coco_archive from COCO C sources staged by fabricate_archive.py.

Run fabricate_archive.py first; do not invoke setup.py directly.
"""

from pathlib import Path
import os

from Cython.Build import cythonize
from setuptools import Extension, setup

HERE = Path(__file__).resolve().parent
C_CORE = HERE / "interface" / "coco.c"
C_HEADER = HERE / "interface" / "coco.h"
if not (C_CORE.is_file() and C_HEADER.is_file()):
    raise RuntimeError(
        "Missing generated COCO C core. Run: "
        "python fabricate_archive.py --coco-experiment /path/to/coco-experiment"
    )

archive_extension = Extension(
    "cocoprep.coco_archive",
    sources=[str(HERE / "interface" / "coco_archive.pyx"), str(C_CORE)],
    include_dirs=[str(HERE / "interface")],
    extra_compile_args=["-std=c99"] if os.name != "nt" else [],
    libraries=["m"] if os.name != "nt" else [],
)

setup(
    name="cocoprep",
    version="0.2.0",  # The packaging version is independent of the COCO core version.
    description="COCO C-backed bi-objective archive preprocessing",
    packages=["cocoprep"],
    package_dir={"cocoprep": "python"},
    ext_modules=cythonize([archive_extension], compiler_directives={"language_level": 3}),
    python_requires=">=3.9",
)
