# Working on pytrnsys_gui

For the developer setup (virtual environment in `venv`, requirements, generated Qt files), see "Installation from source / Developer installation" in `README.md`.

## Checks

1. Run the static checks the way CI does: `venv\Scripts\python dev-tools\devTools.py -s` (mypy, pylint, and `black -l 79 --check`).
2. Format with `black -l 79`, not black's default line length: there's no black configuration file, the line length is only set in `dev-tools/devTools.py`.

## Tests

1. Some tests write their outputs (`.dck`, `.prt`, `results/`, ...) into the test data folders under `tests/`, and some of them fail when those outputs already exist, e.g. `testHydraulicModesGui.py::testRunModesInvalidDckUnmodifiedDlls`. Before rerunning the suite, remove the untracked files there (`git clean -n tests` to see them first).
