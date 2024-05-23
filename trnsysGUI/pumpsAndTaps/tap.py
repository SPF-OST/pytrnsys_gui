import os as _os
import shutil as _su
import typing as _tp

from PyQt5.QtWidgets import QTreeView

import trnsysGUI.MyQFileSystemModel as _fs
import trnsysGUI.MyQTreeView as _tv
import trnsysGUI.connection.connectorsAndPipesExportHelpers as _ehelpers
import trnsysGUI.connection.hydraulicExport.common as _hecom
import trnsysGUI.images as _img
import trnsysGUI.massFlowSolver.networkModel as _mfn
import trnsysGUI.temperatures as _temps
from . import _tapBase


class Tap(_tapBase.TapBase):
    def __init__(self, trnsysType: str, editor, displayName: str) -> None:
        super().__init__(trnsysType, editor, _mfn.PortItemDirection.INPUT, displayName)

        self.loadedFiles: list[str] = []
        self.addTree()

    @classmethod
    @_tp.override
    def hasDdckPlaceHolders(cls) -> bool:
        return True

    def _getImageAccessor(self) -> _tp.Optional[_img.ImageAccessor]:
        return _img.TAP_SVG

    def _getCanonicalMassFlowRate(self) -> float:
        return -self._massFlowRateInKgPerH

    def exportPipeAndTeeTypesForTemp(self, startingUnit: int) -> _tp.Tuple[str, int]:
        fromAdjacentHasPiping = _hecom.getAdjacentConnection(self._graphicalPortItem)

        inputTemperature = _ehelpers.getTemperatureVariableName(
            fromAdjacentHasPiping.hasInternalPiping,
            fromAdjacentHasPiping.sharedPort,
            _mfn.PortItemType.STANDARD,
        )

        tapTemperature = _temps.getTemperatureVariableName(
            shallRenameOutputInHydraulicFile=False,
            componentDisplayName=self.displayName,
            nodeName=self._modelTerminal.name,
        )

        equation = f"""\
EQUATIONS 1
{tapTemperature} = {inputTemperature}

"""
        return equation, startingUnit

    def addTree(self):
        """
        When a blockitem is added to the main window.
        A file explorer for that item is added to the right of the main window by calling this method
        """
        self.logger.debug(self.editor)
        pathName = self.displayName
        self.path = self.editor.projectFolder
        self.path = _os.path.join(self.path, "ddck")
        self.path = _os.path.join(self.path, pathName)
        if not _os.path.exists(self.path):
            _os.makedirs(self.path)

        self.model = _fs.MyQFileSystemModel()
        self.model.setRootPath(self.path)
        self.model.setName(self.displayName)
        self.tree = _tv.MyQTreeView(self.model, self)
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(self.path))
        self.tree.setObjectName(f"{self.displayName}Tree")
        for i in range(1, self.model.columnCount() - 1):
            self.tree.hideColumn(i)
        self.tree.setMinimumHeight(200)
        self.tree.setSortingEnabled(True)
        self.editor.splitter.addWidget(self.tree)

    def deleteBlock(self):
        """
        Overridden method to also delete folder
        """
        self.logger.debug("Block " + str(self) + " is deleting itself (" + self.displayName + ")")
        self.editor.trnsysObj.remove(self)
        self.logger.debug("deleting block " + str(self) + self.displayName)
        self.editor.diagramScene.removeItem(self)
        widgetToRemove = self.editor.findChild(QTreeView, self.displayName + "Tree")
        _su.rmtree(self.path)
        self.deleteLoadedFile()
        try:
            widgetToRemove.hide()
        except AttributeError:
            self.logger.debug("Widget doesnt exist!")
        else:
            self.logger.debug("Deleted widget")
        del self

    def setDisplayName(self, newName):
        """
        Overridden method to also change folder name
        """
        self.displayName = newName
        self.label.setPlainText(newName)
        self.model.setName(self.displayName)
        self.tree.setObjectName(f"{self.displayName}Tree")
        self.logger.debug(_os.path.dirname(self.path))
        destPath = _os.path.join(_os.path.split(self.path)[0], self.displayName)
        if _os.path.exists(self.path):
            _os.rename(self.path, destPath)
            self.path = destPath
            self.logger.debug(self.path)

    def _setUnFlippedPortPos(self, delta: int) -> None:
        self.origInputsPos = [[0, delta]]
        self._graphicalPortItem.setPos(self.origInputsPos[0][0], self.origInputsPos[0][1])
