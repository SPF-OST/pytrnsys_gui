# pylint: skip-file

import os
import shutil
import typing as _tp

from PyQt5.QtWidgets import QTreeView

import trnsysGUI.images as _img
import trnsysGUI.internalPiping as _ip
import trnsysGUI.massFlowSolver.networkModel as _mfn
from trnsysGUI.BlockItemFourPorts import BlockItemFourPorts
from trnsysGUI.MyQFileSystemModel import MyQFileSystemModel  # type: ignore[attr-defined]
from trnsysGUI.MyQTreeView import MyQTreeView  # type: ignore[attr-defined]


class ExternalHx(BlockItemFourPorts):
    def __init__(self, trnsysType, parent, **kwargs):
        super().__init__(trnsysType, parent, **kwargs)

        self.loadedFiles = []

        self.w = 80
        self.h = 120

        self.changeSize()
        self.addTree()

    def _getImageAccessor(self) -> _tp.Optional[_img.ImageAccessor]:
        return _img.EXTERNAL_HX_SVG

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
        lw, lh = rect.width(), rect.height()
        lx = (w - lw) / 2
        self.label.setPos(lx, h)

        self.origInputsPos = [[0, delta], [w, h - delta]]
        self.origOutputsPos = [[0, h - delta], [w, delta]]
        self.inputs[0].setPos(self.origInputsPos[0][0], self.origInputsPos[0][1])
        self.inputs[1].setPos(self.origInputsPos[1][0], self.origInputsPos[1][1])
        self.outputs[0].setPos(self.origOutputsPos[0][0], self.origOutputsPos[0][1])
        self.outputs[1].setPos(self.origOutputsPos[1][0], self.origOutputsPos[1][1])

        self.updateFlipStateH(self.flippedH)
        self.updateFlipStateV(self.flippedV)

        self.inputs[0].side = (self.rotationN + 2 * self.flippedH) % 4
        self.inputs[1].side = (self.rotationN + 2 - 2 * self.flippedH) % 4

        self.outputs[0].side = (self.rotationN + 2 * self.flippedH) % 4
        self.outputs[1].side = (self.rotationN + 2 - 2 * self.flippedH) % 4

        return w, h

    def addTree(self):
        """
        When a blockitem is added to the main window.
        A file explorer for that item is added to the right of the main window by calling this method
        """
        self.logger.debug(self.parent.parent())
        pathName = self.displayName
        if self.parent.parent().projectPath == "":
            self.path = self.parent.parent().projectFolder
        else:
            self.path = self.parent.parent().projectPath
        self.path = os.path.join(self.path, "ddck")
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
        self.parent.parent().splitter.addWidget(self.tree)

    def deleteBlock(self):
        """
        Overridden method to also delete folder
        """
        self.logger.debug("Block " + str(self) + " is deleting itself (" + self.displayName + ")")
        self.parent.parent().trnsysObj.remove(self)
        self.logger.debug("deleting block " + str(self) + self.displayName)
        self.parent.scene().removeItem(self)
        widgetToRemove = self.parent.parent().findChild(QTreeView, self.displayName + "Tree")
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

    def getInternalPiping(self) -> _ip.InternalPiping:
        side1Input = _mfn.PortItem("In", _mfn.PortItemDirection.INPUT)
        side1Output = _mfn.PortItem("Out", _mfn.PortItemDirection.OUTPUT)
        side1Pipe = _mfn.Pipe(side1Input, side1Output, name="Side1")

        side2Input = _mfn.PortItem("In", _mfn.PortItemDirection.INPUT)
        side2Output = _mfn.PortItem("Out", _mfn.PortItemDirection.OUTPUT)
        side2Pipe = _mfn.Pipe(side2Input, side2Output, name="Side2")

        modelPortItemsToGraphicalPortItem = {
            side1Input: self.inputs[0],
            side1Output: self.outputs[0],
            side2Input: self.inputs[1],
            side2Output: self.outputs[1]
        }

        return _ip.InternalPiping([side1Pipe, side2Pipe], modelPortItemsToGraphicalPortItem)
