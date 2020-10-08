.. _file-tree:

The file structure of a project
*******************************

Opening or creating a project
-----------------------------

Each project that can be edited with the GUI is connected to a folder, which in the
follwing will be called ``SPF_awesome`` as an example. When the GUI is started the user
is asked whether they want to create a new project or open an exisiting one. When a new
project is created a dialogue guides the user through the creation of a new project
folder. Saving a diagram is accomplished through the generation of a json-file inside
``SPF_awesome``, that has the same name. This means that in order to open the existing
project of the name ``SPF_awesome`` the following file needs to be opened::

    ..\SPF_awesome\SPF_awesome.json

All files that need to be loaded for the project or which are generated from the GUI are
saved in ``SPF_awesome``.

Default file structure
----------------------

When a project is initialized the following file structure is created:

.. image:: ./resources/defaultFiles.png
        :width: 400
        :alt: defaultFiles

The folder called ``ddck`` contains the folder ``generic``, into which the generic
ddck-files ``head.ddck`` and ``end.ddck`` are loaded. Furthermore, the empty folders
``control``, ``hydraulic``, and ``weather`` are created. These are folders for
ddck-files that are not directly connected to any components in a project diagram. The
project folder also contains ``run.config``, which is a template that can be altered
by the user.

ddck folders
------------

In the following different folders are described, which can be found in::

    .\SPF_awesome\ddck

Square brackets indicate place holders for component names.

``generic``

    This folder is created when a project is initialized and contains ``head.ddck``
    and ``end.dck``, which contain the information that needs to be added at the
    beginning and the end of a dck-file respectively.

``[storage tank]``

    As soon as a storage tank is dropped in the diagram, a folder of the same name is
    created. Its name changes dynamically with the name of the storage tank. When the
    ddck-file of the storage tank is exported, it will build the following two
    files::

        .\ddck\[storage tank]\[storage tank].ddck
        .\ddck\[storage tank]\[storage tank].ddcx

    Here the file with the extension ``.ddck`` contains the information of the storage
    tank, that is needed to build the dck-file. Meanwhile, the file with the extension
    ``.ddcx`` contains the black box component temperature equations, which are needed
    to build ``hydraulic.ddck`` (see below).

``[component (not a storage tank)]``

    As soon as a component that requires one or more ddck-files for a simulation is
    dropped in the diagram, a folder of the same name is created. Its name changes
    dynamically with the name of the component. The user needs to load the
    ddck-file(s) that represent the component in question into the corresponding
    folder.

``hydraulic``

    This folder is created when a project is initialized. It is the default export
    destination for ``hydraulic.ddck``.

``control``

    This folder is created when a project is initialized. The user should load all
    ddck-files which represent control features into this folder.