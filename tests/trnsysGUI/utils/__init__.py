import collections.abc as _abc
import pytrnsys.utils.log as _ulog

import trnsysGUI.blockItemHasInternalPiping as bip
import trnsysGUI.project as prj
import trnsysGUI.mainWindow as mw


def createMainWindow(projectFolder, projectName):
    projectJsonFilePath = projectFolder / f"{projectName}.json"
    project = prj.LoadProject(projectJsonFilePath)
    logger = _ulog.getOrCreateCustomLogger("root", "DEBUG")  # type: ignore[attr-defined]
    mainWindow = mw.MainWindow(logger, project)  # type: ignore[attr-defined]
    mainWindow.showBoxOnClose = False
    mainWindow.editor.forceOverwrite = True

    return mainWindow


def getDesiredTrnsysObjectFromList(
    trnsysObjs: _abc.Sequence[bip.BlockItemHasInternalPiping],
    desiredBlockItem: bip.BlockItemHasInternalPiping,
):
    for trnsysObj in trnsysObjs:
        if isinstance(type(trnsysObj), type(desiredBlockItem)):
            return trnsysObj
    return None
