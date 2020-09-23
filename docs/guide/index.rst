.. _project-folders:

GUI projects
============

Project Folders
***************

Opening or creating a project
-----------------------------

Each project that can be edited with the GUI is connected to a folder, which in the
follwing will be called ``SPF_awesome`` as an example. When the GUI is started the user
is asked whether they want to create a new project or open an exisiting one. When a new
project is created a dialogue guides the user through the creation of a new project
folder. Saving a diagram is accomplished through the generation of a json-file inside
``SPF_awesome``, that has the same name. This means that in order to open the existing
project of the name ``SPF_awesome`` the following file needs to be opened::

    ../SPF_awesome/SPF_awesome.json

All files that need to be loaded for the project or which are generated from the GUI are
saved in ``SPF_awesome``. When a project is initialized a subfolder called ``ddck`` is
created, which already contains the generic ddck-files ``head.ddck`` and ``end.ddck``,
and into which the ddck-files corresponding to the components will be added later on.
When a pdf of the diagram is exported or a dck-file is generated, the respective files
are also saved in ``SPF_awesome``.