.. _interface:

The user interface
==================

The user interface consists of a menu bar, a tool bar, and three main widgets. The
center and the main widget of the interface is the diagram. Here different components
can be placed and connected. The available components can be found in the widget on
the lefthand side and can simply be dragged into the diagram to be placed. On the
righthand widget the file tree of the ``ddck``-folder can be seen. For each component
dropped into the diagram an additional folder is created in this tree.

.. image:: ./resources/interface.png
        :width: 2000
        :alt: interface

Making a diagram
----------------

Loading ddck-files
------------------

The toolbar
-----------

``Save``

    .. image:: C:/Daten/GIT/pytrnsys_gui/trnsysGUI/images/inbox.png
        :width: 50
        :alt: save

    Saves the current diagram to a json-file in the project folder.

``Open``

    .. image:: C:/Daten/GIT/pytrnsys_gui/trnsysGUI/images/outbox.png
        :width: 50
        :alt: open

    Opens a diagram from a json-file.

``Zoom in``

    .. image:: C:/Daten/GIT/pytrnsys_gui/trnsysGUI/images/zoom-in.png
        :width: 50
        :alt: zoom in

    Zoom into diagram.

``Zoom out``

    .. image:: C:/Daten/GIT/pytrnsys_gui/trnsysGUI/images/zoom-out.png
        :width: 50
        :alt: zoom out

    Zoom out of diagram.

``Toggle labels``

    .. image:: C:/Daten/GIT/pytrnsys_gui/trnsysGUI/images/labelToggle.png
        :width: 50
        :alt: toggle labels

    Toggle the labels of the components and pipes.

``Start visualization of mass flows``

    .. image:: C:/Daten/GIT/pytrnsys_gui/trnsysGUI/images/runMfs.png
        :width: 50
        :alt: visualize mass flows

    Creates a dck-file for the diagram and runs TRNSYS from it, and then shows a
    visualization of the mass flows in the diagram.

``Export hydraulic.ddck``

    .. image:: C:/Daten/GIT/pytrnsys_gui/trnsysGUI/images/exportHydraulics.png
        :width: 50
        :alt: export hydraulic.ddck

    Exports the following file::

        ..\ddck\hydraulic\hydraulic.ddck

    This file contains the information

    Here, ``hydraulic.ddck`` contains the information of the hydraulics of the
    diagram, while ``nameOfStorageTank.ddcx``::

        ..\ddck\nameOfStorageTank\nameOfStorageTank.ddcx

