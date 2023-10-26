import multiprocessing as _mp

import trnsysGUI.gui as _gui

if __name__ == "__main__":
    # Support freezing using PyInstaller, see
    # https://github.com/pyinstaller/pyinstaller/wiki/Recipe-Multiprocessing and
    # https://docs.python.org/3/library/multiprocessing.html#multiprocessing.freeze_support
    _mp.freeze_support()

    _gui.main()
