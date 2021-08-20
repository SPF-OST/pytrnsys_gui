# Graphical user interface for pytrnsys

## Documentation

You can find the documentation under https://spf-ost.github.io/pytrnsys_gui/ 

## Installation

In the following all commands should be run from the `pytrnsys_gui` directory. The command should be run in a 
"Windows Command Prompt" for Windows environment. The commands should be very similar should you wish to install on
Linux.

### Binary installation / User installation

#### Prerequisites

##### Required

1. [Python 3.9](https://www.python.org/downloads/)

#### Getting started

A video guiding through the following steps can be found on [YouTube](https://www.youtube.com/watch?v=c8VPmOCeQN8).

1. Open a command prompt (e.g., by hitting the Windows-key, then typing "cmd" 
   into the search box and hitting enter). The following commands should be entered
   into the command prompt just opened.

1. Navigate to the directory which should contain the `pytrnsys-gui` directory:
    ```commandline
    cd [your-directory]
    ```
   Replace `[your-directory]` (including the brackets []) with your directory of choice: if your
directory is called `foo` then `pytrnsys-gui` will be installed to `foo\pytrnsys-gui`.
   
1. Create a virtual environment:
    ```commandline
    py -3.9 -m venv pytrnsys-gui
    ```
1. Activate it:
    ```commandline
    pytrnsys-gui\Scripts\activate
    ```
1. Install the `wheel` package:
    ```commandline
    pip install wheel
    ```
         
1. Install `pytrnsys-gui` and its requirements:
    ```commandline
    pip install -r https://raw.githubusercontent.com/SPF-OST/pytrnsys_gui/master/requirements/releases/v0.9.5/requirements.txt
    ```
   (Note: In the [YouTube video](https://www.youtube.com/watch?v=c8VPmOCeQN8) the version is replaced manually, this is
   not necessary anymore, when copying the command line above.)
   
You can now close the command prompt opened in the first step.

The `pytrnsys-gui` can now be started by double-clicking on the 
`pytrnsys-gui\Scripts\pytrnsys-gui.exe` file. Example projects can be found in the
`pytrnsys-gui\pytrnsys_gui_data\examples` directory.


#### Upgrading from one patch version to the next within the same minor version
There is a shortcut for upgrading from one patch version to the next within the same minor version, e.g., from
1.2.11 to 1.2.12:

1. Activate your virtual environment:
    ```commandline
    pytrnsys-gui\Scripts\activate

1. Issue the following command:
    ```commandline
    pip install --upgrade pytrnsys-gui
   
This method might not be 100% reliable. If you're experiencing problems, we recommend installing your preferred
version from scratch as described above.


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

All the following commands should be run from the `pytrnsys_gui` directory. The commands
specified are for a Windows environment. They are very similar for Linux.

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
1. Run `pytrnsys-gui`!
    ```commandline
    cd trnsysGUI
    python GUI.py
    ```
    
Beware that the GUI can only be started from within the virtual environment you created in step 1. 
I.e., whenever you open a new console window from which you want to start the GUI you first need 
to activate the environment (step 2. above).

