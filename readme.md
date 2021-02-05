Graphical user interface for pytrnsys
=====================================

Documentation
-------------

You can find the documentation under https://spf-ost.github.io/pytrnsys_gui/ 

Prerequisites
-------------

Compulsive:
* A local clone of https://github.com/SPF-OST/pytrnsys.git

Assumed for the instructions in the following (different frameworks can be used individually):
* Anaconda installation
* PyCharm editor

Getting started
---------------

Open an Anaconda prompt and navigate to your local pytrnsys_gui repository:
````
cd ...\GIT\pytrnsys_gui
````
Then enter the following:
````
conda env create -f gui_env.yml
````
This will create a virtual environment 'trnsys3.7'. Next, enter:
````
conda info --envs
````
This will show you your virtual environments for python. Note where 'trnsys3.7' is located.

Now launch PyCharm and open your pyrtnsys_gui repository. Then go to File > Settings > Project: pytrnsys_gui > Project 
Interpreter. Click on the gearwheel icon on the right of the dropdown menu and select 'Add...'. In the window that opens
select 'Existing environment'. In the line 'Interpreter' browse to the folder of 'trnsys3.7' (noted from before) and 
select 'python.exe' from within this folder. This will set up 'trnsys3.7' as the virtual environment for your local 
pytrnsys_gui repository.

Go back to the Project Interpreter menu, click again on the gearwheel icon, and select 'Show All...'. Select 'trnsys3.7'
 on the list that opens and click on the path icon on the right ('Show paths for the selected interpreter'). In the 
 window that opens click on the '+' and select the folder of your local repository of 
 https://github.com/SPF-OST/pytrnsys.git:
 ````
...\GIT\pytrnsys
````
 
Now your virtual environment to run the graphical user interface is set. Run 'GUI.py'. This should open the graphical 
user interface. Sometimes the opening dialogue is behind other windows, so make sure to check behind those, if you don't
 see it immediately.