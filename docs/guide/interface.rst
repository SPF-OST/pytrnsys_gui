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

    Creates the following file for the diagram::

        ..\[project name]\[project name]_mfs.dck

    Afterwards, it runs TRNSYS from this file, and then shows a visualization of the
    mass flows in the diagram.

``Export hydraulic.ddck``

    .. image:: C:/Daten/GIT/pytrnsys_gui/trnsysGUI/images/exportHydraulics.png
        :width: 50
        :alt: export hydraulic.ddck

    Exports the following files::

        ..\ddck\hydraulic\hydraulic.ddck
        ..\ddck\control\valve_control.ddck

    These files contain the information about the hydraulics of the system. The
    so-called black box component output equations are loaded to ``hydraulic.ddck``
    from::

        ..\ddck\[storage tank]\[storage tank].ddcx

    If this file does not exist yet, when ``hydraulic.ddck`` is exported, the export
    of the storage tank will be triggered.

``Update run.config``

    .. image:: C:/Daten/GIT/pytrnsys_gui/trnsysGUI/images/updateConfig.png
        :width: 50
        :alt: update run.config

    Updates the following entries in ``run.config``::

        string PROJECT$
        string projectPath

    and the used ddcks (from the current content of the ``ddck``-folder).

``Export dck``

    .. image:: C:/Daten/GIT/pytrnsys_gui/trnsysGUI/images/exportDck.png
        :width: 50
        :alt: export dck

    Exports::

        ..\[project name]\[project name].dck

    according to what is specified in ``run.config``.

``Run simulation``

    .. image:: C:/Daten/GIT/pytrnsys_gui/trnsysGUI/images/runSimulation.png
        :width: 50
        :alt: run simulation

    Exports the dck-file like above and launches a simulation with Trnsys.

``Delete diagram``

    .. image:: C:/Daten/GIT/pytrnsys_gui/trnsysGUI/images/trash.png
        :width: 50
        :alt: delete diagram

    Deletes the current diagram.