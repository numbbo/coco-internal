# COCO preprocessing

This directory contains the original preprocessing workflows:

- `archive-update/` merges and thins bi-objective archives and computes
  the normalized hypervolume values used when updating COCO references.
- `log-reconstruction/` replays archived objectives through `cocoex` and
  reconstructs logger output, for example after a reference update.

The archive tools use the **compiled C-backed** Python module
`cocoprep.coco_archive`; log reconstruction uses the normal `cocoex` Python
package. The archive module is built from the **current COCO experiment C
sources**, using COCO's `scripts/fabricate` workflow, not the deprecated
`setup.py.in` template from the old monorepo.

## Setup

Use Python 3.9+ with a working C compiler and a checkout of
[`numbbo/coco-experiment`](https://github.com/numbbo/coco-experiment).
For example, from a directory containing both repositories:

```bash
git clone https://github.com/numbbo/coco-experiment.git
python -m pip install -U pip setuptools wheel 'Cython>=3' pytest coco-experiment
python coco-internal/code-preprocessing/archive-update/fabricate_archive.py \
  --coco-experiment ./coco-experiment --editable
```

`fabricate_archive.py` invokes `coco-experiment/scripts/fabricate`, stages
its generated `coco.c` and `coco.h` in `archive-update/interface/`, and then
installs the compiled `cocoprep` extension into your active Python environment.
`--editable` is convenient for development. This is a one-time build, unless
you change the COCO checkout or the archive interface. A standalone wheel is
still recommended for deployment. Compilation is **required for `cocoprep`**:
`fabricate` generates sources, and setuptools/Cython compile the extension.

Check the imports:

```bash
python -c "import cocoex; from cocoprep.coco_archive import Archive; print('COCO imports OK')"
```

See [`archive-update/README.md`](archive-update/README.md) for a more detailed
build explanation and archive examples.

## Run

From the `coco-internal` repository root, examples using the included fixtures:

```bash
python code-preprocessing/archive-update/archive_update.py \
  --merge-only ./merged \
  code-preprocessing/archive-update/test-data/archives-input

python code-preprocessing/archive-update/archive_thinning.py \
  -p 1e-3 ./thinned ./merged

python code-preprocessing/log-reconstruction/log_reconstruct.py --help
```

For more configuration flags run any preprocessing script with `--help`.
The reconstruction script requires `cocoex` and replays values through
`Problem.logger_biobj_feed_solution`, not the separate `cocoprep` archive.

## Tests

```bash
python -m pytest -q code-preprocessing/archive-update/test_archives.py
python -m pytest -q code-preprocessing/archive-update/test_fabricate_archive.py
```

`test_archives.py` uses the real compiled archive extension and fixture data.
`test_fabricate_archive.py` verifies the build pipeline with a simulated C
core; it does **not** prove numerical compatibility with a particular release
of `coco-experiment`. Please run the archive tests against the version of
COCO you intend to use.

To update a COCO release's actual hypervolume reference constants, regenerating
an archive table alone is insufficient: those constants must be incorporated
into a newly built `cocoex` release before replaying logger outputs.
