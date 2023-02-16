# Graphical user interface for pytrnsys

[![Coverage Status](https://coveralls.io/repos/github/SPF-OST/pytrnsys_gui/badge.svg?branch=master)](https://coveralls.io/github/SPF-OST/pytrnsys_gui?branch=master)

## Overview

A short presentation (15 min) of pytrnsys and its features can be found in the following 
[YouTube video](https://www.youtube.com/watch?v=B1BSjYRKuVM).

## Documentation

You can find the documentation under https://pytrnsys.readthedocs.io/ 

## Installation

You'll need `TRNSYS` (at least version 17, preferably version 18, 32 bit)  installed on your machine.

### Binary installation / User installation

#### Installation

##### Latest stable release

This version is recommended for **non-SPF users** and/or everyone interested in the most recent stable release
possibly missing the latest features.

Go to [Releases](https://github.com/SPF-OST/pytrnsys_gui/releases) and download the `.zip` file included in
the latest Release Build:

![Latest Versioned Release](doc/release.png)

(Note that the version will vary as newer versions are being published)

##### Bleeding-edge version

This version is recommended for **SPF users** and/or everyone wanting to get the latest and greatest but not minding the fact
that this version is less stable (i.e. can contain more bugs/errors) than the latest stable release.

Go to [Releases](https://github.com/SPF-OST/pytrnsys_gui/releases) and download the `.zip` file included in
the `bleeding-edge` Development Build:

![Bleeding Edge Release](doc/bleeding-edge.png)

#### Post-installation

Copy `pytrnsys` custom TRNSYS types in the form of compiled DLLs from

    pytrnsys_data\data\ddcks\dlls
    
to the respective folder of your TRNSYS installation:

    ...\UserLib\ReleaseDLLs

#### Troubleshooting
`pytrnsys-gui.exe` writes logging messages into the `pytrnsys-gui.log` file located in the same directory
as the `.exe` file. The `.log` file might give you some hints as to what happened if something doesn't
work or if `pytrnsys-gui.exe` has crashed.


### Installation from source / Developer installation

#### Prerequisites

##### Required

1. [Python 3.9](https://www.python.org/downloads/)
1. Local clones of the following GIT repositories:
    1. `https://github.com/SPF-OST/pytrnsys.git`
    1. `https://github.com/SPF-OST/pytrnsys_gui.git`

    They should be next to each other and be called `pytrnsys` and `pytrnsys_gui` like so:
    ```
    parent/
      pytrnsys/
      pytrnsys_gui/
    ```

##### Recommended
* [PyCharm Community IDE](https://www.jetbrains.com/pycharm/downloa)

#### Getting started

All the following commands should be run from the `pytrnsys_gui` directory. The command should be run in a 
"Windows Command Prompt" (cmd).

1. Create a virtual environment:
    ```commandline
    py -3.9 -m venv venv
    ```
2. Activate it:
    ```commandline
    venv\Scripts\activate
    ```
3. Install the requirements:
    ```commandline
    pip install wheel
    python -m pip install -r requirements\dev.txt
    ```
4. Generate Python files from the include Qt creator files:
   ```commandline
   python dev-tools\generateGuiClassesFromQtCreatorStudioUiFiles.py
   ```
5. Tag the editable install of `pytrnsys-gui`
   ```commandline
   python setup.py egg_info -b dev
   ```
   (By adding this tag we make sure that the Qt Creator .ui files are re-generated each time the GUI is started.)
6. Now you can run `pytrnsys-gui`!
    ```commandline
    cd trnsysGUI
    python GUI.py
    ```

Several custom TRNSYS types in the form of compiled DLLs are delivered with `pytrnsys`.

You'll have to manually copy the files from

    pytrnsys\data\ddcks\dlls
    
to the respective folder of your TRNSYS installation:

    ...\UserLib\ReleaseDLLs
    
Beware that the GUI can only be started from within the virtual environment you created in step 1. 
I.e., whenever you open a new console window from which you want to start the GUI you first need 
to activate the environment (step 2. above).

