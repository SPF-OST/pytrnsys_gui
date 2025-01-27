import logging as _log
import typing as _tp

import PyQt5.QtWidgets as _qtw

import trnsysGUI.diagram.Editor as _de
import trnsysGUI.project as _prj


def createDiagramEditor(
    project: _prj.Project, parent: _qtw.QWidget, logger: _log.Logger
) -> _de.Editor:
    match project:
        case _prj.LoadProject():
            return _de.Editor(
                parent,
                projectFolder=str(project.jsonFilePath.parent),
                jsonPath=None,
                loadValue="load",
                logger=logger,
            )
        case _prj.MigrateProject():
            return _de.Editor(
                parent,
                str(project.newProjectFolderPath),
                str(project.oldJsonFilePath),
                loadValue="json",
                logger=logger,
            )
        case _prj.CreateProject():
            return _de.Editor(
                parent,
                projectFolder=str(project.jsonFilePath.parent),
                jsonPath=str(project.jsonFilePath),
                loadValue="new",
                logger=logger,
            )
        case _:
            _tp.assert_never(project)
