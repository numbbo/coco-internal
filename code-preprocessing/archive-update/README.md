# Build and use the C-backed bi-objective archive

The `cocoprep.coco_archive.Archive` class is the original Cython binding to
COCO's `coco_archive_*` functions. The archive functions are **not** exposed
by the public Python `cocoex` API, so the archive gets its own small compiled
extension while logger reconstruction uses `cocoex` directly.

## Prerequisites

- Python 3.9+ with `pip`, `setuptools`, `wheel`, and Cython 3+;
- a C99 compiler supported by your Python installation;
- the `coco-experiment` source checkout. The Python distribution from PyPI
  supplies `cocoex`, but **does not supply the stand-alone generated C sources**
  needed for this additional extension.

Example, from the parent of `coco-internal` and `coco-experiment`:

```bash
python -m pip install -U setuptools wheel 'Cython>=3' coco-experiment colorama toml six
python code-preprocessing/archive-update/fabricate_archive.py --coco-experiment ./coco-experiment --editable
```

The helper does the following:

1. Runs **`python coco-experiment/scripts/fabricate`** using your Python
   interpreter, generating/updating COCO's current amalgamated C core.
2. Locates `build/c/coco.c` and `coco.h` (or `build/python/cython/` for layouts
   that provide these files there), and checks the required archive symbols
   in the generated header.
3. Copies the generated C source and header into `interface/` (ignored by Git).
4. Runs `python -m pip install .` (or `pip install --editable .`), using the
   local `pyproject.toml` / `setup.py` to compile the original `Archive`
   Cython class against that generated core.

To generate/stage without installing, add `--prepare-only`. To build offline
with dependencies already installed, add `--no-build-isolation`.
`--skip-fabricate` is available when previously generated COCO C sources have
already been validated; by default the upstream generator is always rerun.

**Important:** Fabricate is a *source-generation* step, not a compiler or a
linker. Cython and a C compiler are still required once for this extension.
The compiled module embeds a separate copy of the COCO C core and does not
link against private symbols in the installed `cocoex` extension. Use the
same `coco-experiment` revision as the `cocoex` package for consistent values.

## Python API

```python
import cocoex
from cocoprep.coco_archive import Archive

archive = Archive('bbob-biobj', 1, 4, 2)
archive.add_solution(1.0, 2.0, '1 1.0 2.0')
print(archive.number_of_solutions, archive.hypervolume)
while True:
    line = archive.get_next_solution_text()
    if line is None:
        break
    print(line)
```

The order is `(suite_name, function, instance, dimension)` to match the
original class, even though COCO's lower-level C constructor uses a different
argument order. The archive is initialized by COCO with two extreme solutions;
`hypervolume` and solution iteration preserve the C implementation's
semantics. The extended bi-objective suite name is handled automatically for
functions 56–92.

## Run scripts

From the checkout root:

```bash
cd code-preprocessing/archive-update
python archive_update.py --merge-only ./merged test-data/archives-input
python archive_thinning.py -p 1e-6 ./thinned merged
cd ..
```

For additional filters use `--help` on either tool. Source code still imports
`from cocoprep.coco_archive import Archive, log_level` as before.

## Validate

```bash
python -c "from cocoprep.coco_archive import Archive; print(Archive('bbob-biobj', 1, 4, 2).hypervolume)"
```

The build pipeline tests use a simulated C core to check generation,
compilation, packaging and import. For real numerical results the genuine
`coco-experiment` checkout is required. If an upstream release removes any
`coco_archive_*` functions, the helper stops with an API compatibility error
instead of building against a misleading substitute.
