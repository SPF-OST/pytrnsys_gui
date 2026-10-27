# Working on pytrnsys_gui

For setup, checks and tests, see `DEVELOPER-README.md`.

## Pitfalls

1. Don't import a test class (e.g. `TestEditor` from `tests/trnsysGUI/diagram/testEditor.py`) into another test
   module to reuse its helpers: pytest then also collects and runs the whole class there. Copy the helper instead.
