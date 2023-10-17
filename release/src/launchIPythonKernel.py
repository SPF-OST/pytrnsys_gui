"""
Copied from
https://github.com/ipython/ipykernel/blob/515004a331b10dff026b8d81a0571e4cdf1847a3/ipykernel_launcher.py
"""

import sys

if __name__ == "__main__":
    # Remove the CWD from sys.path while we load stuff.
    # This is added back by InteractiveShellApp.init_path()
    if sys.path[0] == "":
        del sys.path[0]

    from ipykernel import kernelapp as app

    app.launch_new_instance()
