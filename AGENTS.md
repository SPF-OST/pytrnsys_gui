# Working on pytrnsys_gui

For setup, checks and tests, see `DEVELOPER-README.md`; for how the code is organized, see `ARCHITECTURE.md`.

## Keeping docs current

1. When a change makes `ARCHITECTURE.md` or `DEVELOPER-README.md` wrong or outdated, update it in the same commit.

## Pitfalls

1. Don't import a test class (e.g. `TestEditor` from `tests/trnsysGUI/diagram/testEditor.py`) into another test
   module to reuse its helpers: pytest then also collects and runs the whole class there. Copy the helper instead.
