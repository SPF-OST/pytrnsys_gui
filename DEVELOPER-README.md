## Installation from source / Developer installation

#### Prerequisites

##### Required

1. [Python 3.12](https://www.python.org/ftp/python/3.12.2/python-3.12.2-amd64.exe): !!ENSURE LONG PATHS ARE ENABLED!!
1. Enable long paths in the Terminal:
   ```commandline
      New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force
   ```
1. Enable long paths in git (system is for CI servers, global is for User):
   ```commandline
      git config --system core.longpaths true
      git config --global core.longpaths true
   ```
1. Local clones of the following GIT repositories:
    1. `https://github.com/SPF-OST/pytrnsys.git`
    1. `https://github.com/SPF-OST/pytrnsys_gui.git`

    They should be next to each other and be called `pytrnsys` and `pytrnsys_gui` like so:
    ```
    parent/
      pytrnsys/
      pytrnsys_gui/
    ```
1. Make sure Inkscape is installed, and the Inkscape/bin is added to the system environmental variables.

##### Recommended
* [PyCharm Community IDE](https://www.jetbrains.com/pycharm/download)

#### Getting started

All the following commands should be run from the `pytrnsys_gui` directory. The command should be run in a 
"Windows Command Prompt" (cmd).

1. Create a virtual environment:
    ```commandline
    py -3.12 -m venv venv
    ```
2. Activate it:
    ```commandline
    venv\Scripts\activate
    ```
3. Install the requirements:
    ```commandline
    python -m pip install --upgrade pip
    python -m pip install wheel uv
    python -m uv pip install -r requirements\dev.txt
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
    python trnsysGUI\gui.py
    ```

Several custom TRNSYS types in the form of compiled DLLs are delivered with `pytrnsys`.

You'll have to manually copy the files from

    pytrnsys\data\ddcks\dlls
    
to the respective folder of your TRNSYS installation:

    ...\UserLib\ReleaseDLLs
    
Beware that the GUI can only be started from within the virtual environment you created in step 1. 
I.e., whenever you open a new console window from which you want to start the GUI you first need 
to activate the environment (step 2. above).

## Managing requirements

### Adding new/removing packages and updating package versions pinned in .in files
```commandline
pip-compile-multi --use-cache --backtracking --uv --no-upgrade -d .\requirements\
```

### Upgrading specific package version to latest (e.g. `pytrnsys-process`)
```commandline
pip-compile-multi --use-cache --backtracking --uv -P pytrnsys-process -d .\requirements\
```

### Upgrading all package versions to latest
```commandline
pip-compile-multi --use-cache --backtracking --uv -d .\requirements\
```

## Keeping your virtual environment up to date

### Syncing virtual environment with package versions (of `dev.txt, e.g.)
```commandline
python -m uv pip sync .\requirements\dev.txt
```

## Static checks and unit tests

### Show all `devTools` script options
```commandline
python .\dev-tools\devTools.py --help
```

### Format code with `black` ###
```commandline
python .\dev-tools\devTools.py --black=""
```

### Run static checks and unit tests ###
```commandline
python .\dev-tools\devTools.py -s -u
```
