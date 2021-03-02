# Graphical user interface for pytrnsys

## Documentation

You can find the documentation under https://spf-ost.github.io/pytrnsys_gui/ 

## Prerequisites

### Required:

1. Microsoft Windows
1. [Python 3.9](https://www.python.org/downloads/)
1. Local clones of the following GIT repositories:
    1. `github.com/SPF-OST/pytrnsys.git`
    1. `github.com/SPF-OST/pytrnsys_gui.git`

    They should be next to each other and be called `pytrnsys` and `pytrnsys_gui` like so:
    ```
    parent/
      pytrnsys/
      pytrnsys_gui/
    ```

### Recommended
* [PyCharm Community IDE](https://www.jetbrains.com/pycharm/downloa)

## Getting started

All the following commands should be run from the `pytrnsys_gui` directory.

1. Create a virtual environment:
    ```commandline
    py -3.9 -m venv venv
    ```
1. Activate it:
    ```commandline
    venv\Scripts\activate
    ```
1. Install the requirements:
    ```commandline
    pip install wheel
    pip install -r requirements\dev\requirements.txt
    ```
1. Run `pytrnsys_gui`!
    ```commandline
    cd trnsysGUI
    python GUI.py
    ```

