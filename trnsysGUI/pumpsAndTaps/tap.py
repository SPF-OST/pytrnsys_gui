# pylint: skip-file

import os
import shutil
import typing as _tp

from PyQt5.QtWidgets import QTreeView

import trnsysGUI.createSinglePipePortItem as _cspi
import trnsysGUI.images as _img
import trnsysGUI.internalPiping as _ip
import trnsysGUI.massFlowSolver.networkModel as _mfn
from trnsysGUI.BlockItem import BlockItem
from trnsysGUI.MyQFileSystemModel import MyQFileSystemModel  # type: ignore[attr-defined]
from trnsysGUI.MyQTreeView import MyQTreeView  # type: ignore[attr-defined]


class Tap(BlockItem, _ip.HasInternalPiping):
    def __init__(self, trnsysType, editor, **kwargs):
        super(Tap, self).__init__(trnsysType, editor, **kwargs)
        self.w = 40
        self.h = 40
        self.inputs.append(_cspi.createSinglePipePortItem("i", 0, self))
        self.loadedFiles = []

        self.changeSize()
        self.addTree()

    def getDisplayName(self) -> str:
        return self.displayName

    def hasDdckPlaceHolders(self) -> bool:
        return True

    def shallRenameOutputTemperaturesInHydraulicFile(self):
        return False

    def _getImageAccessor(self) -> _tp.Optional[_img.ImageAccessor]:
        return _img.TAP_SVG

    def changeSize(self):
        w = self.w
        h = self.h

        """ Resize block function """
        delta = 20

        # Limit the block size:
        if h < 20:
            h = 20
        if w < 40:
            w = 40
        # center label:
        rect = self.label.boundingRect()
        lw = rect.width()
        lx = (w - lw) / 2
        self.label.setPos(lx, h)

        self.origInputsPos = [[0, delta]]
        self.inputs[0].setPos(self.origInputsPos[0][0], self.origInputsPos[0][1])

        self.updateFlipStateH(self.flippedH)
        self.updateFlipStateV(self.flippedV)

        self.inputs[0].side = (self.rotationN + 2 * self.flippedH) % 4

        return w, h

    def exportPumpOutlets(self):
        resStr = "T" + self.displayName + " = " + "T" + self.inputs[0].connectionList[0].displayName + "\n"
        equationNr = 1
        return resStr, equationNr

    def getInternalPiping(self) -> _ip.InternalPiping:
        portItem = _mfn.PortItem("In", _mfn.PortItemDirection.INPUT)
        sink = _mfn.TerminalWithFreeFlow(portItem)

        return _ip.InternalPiping([sink], {portItem: self.inputs[0]})

    def addTree(self):
        """
        When a blockitem is added to the main window.
        A file explorer for that item is added to the right of the main window by calling this method
        """
        self.logger.debug(self.editor)
        pathName = self.displayName
        self.path = self.editor.projectFolder
        self.path = os.path.join(self.path, "../ddck")
        self.path = os.path.join(self.path, pathName)
        if not os.path.exists(self.path):
            os.makedirs(self.path)

        self.model = MyQFileSystemModel()
        self.model.setRootPath(self.path)
        self.model.setName(self.displayName)
        self.tree = MyQTreeView(self.model, self)
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(self.path))
        self.tree.setObjectName("%sTree" % self.displayName)
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
        shutil.rmtree(self.path)
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
        self.tree.setObjectName("%sTree" % self.displayName)
        self.logger.debug(os.path.dirname(self.path))
        destPath = os.path.join(os.path.split(self.path)[0], self.displayName)
        if os.path.exists(self.path):
            os.rename(self.path, destPath)
            self.path = destPath
            self.logger.debug(self.path)