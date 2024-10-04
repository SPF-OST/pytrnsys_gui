import pytrnsys.utils.log as _ulog
import collections.abc as _abc

import trnsysGUI.blockItemHasInternalPiping as bip
import trnsysGUI.project as prj
import trnsysGUI.mainWindow as mw

class Utils:
    @staticmethod
    def createMainWindow(projectFolder, projectName):
        projectJsonFilePath = projectFolder / f"{projectName}.json"
        project = prj.LoadProject(projectJsonFilePath)
        logger = _ulog.getOrCreateCustomLogger("root", "DEBUG")  # type: ignore[attr-defined]
        mainWindow = mw.MainWindow(logger, project)  # type: ignore[attr-defined]
        mainWindow.showBoxOnClose = False
        mainWindow.editor.forceOverwrite = True

        return mainWindow

    @staticmethod
    def getDesiredTrnsysObjectFromList(trnsysObjs: _abc.Sequence[bip.BlockItemHasInternalPiping],
                                       desiredBlockItem: bip.BlockItemHasInternalPiping):
        for trnsysObj in trnsysObjs:
            if isinstance(trnsysObj, desiredBlockItem):
                return trnsysObj
