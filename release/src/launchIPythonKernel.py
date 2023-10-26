"""
Copied from
https://github.com/ipython/ipykernel/blob/515004a331b10dff026b8d81a0571e4cdf1847a3/ipykernel_launcher.py
with some modifications.
"""

import multiprocessing as _mp
import sys as _sys

if __name__ == "__main__":
    # Support freezing using PyInstaller, see
    # https://github.com/pyinstaller/pyinstaller/wiki/Recipe-Multiprocessing and
    # https://docs.python.org/3/library/multiprocessing.html#multiprocessing.freeze_support
    _mp.freeze_support()

    # Remove the CWD from sys.path while we load stuff.
    # This is added back by InteractiveShellApp.init_path()
    if _sys.path[0] == "":
        del _sys.path[0]

    from ipykernel import kernelapp as app

    app.launch_new_instance()
