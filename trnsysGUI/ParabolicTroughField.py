# pylint: skip-file
# type: ignore

import os
import shutil
import typing as _tp

from PyQt5.QtWidgets import QTreeView

import trnsysGUI.createSinglePipePortItem as _cspi
import trnsysGUI.images as _img
import trnsysGUI.massFlowSolver.networkModel as _mfn
from trnsysGUI.BlockItem import BlockItem
from trnsysGUI.MyQFileSystemModel import MyQFileSystemModel
from trnsysGUI.MyQTreeView import MyQTreeView
from trnsysGUI.massFlowSolver import InternalPiping, MassFlowNetworkContributorMixin


class ParabolicTroughField(BlockItem, MassFlowNetworkContributorMixin):
    def __init__(self, trnsysType, parent, **kwargs):
        super().__init__(trnsysType, parent, **kwargs)

        self.w = 160
        self.h = 240
        self.inputs.append(_cspi.createSinglePipePortItem("i", 2, self))
        self.outputs.append(_cspi.createSinglePipePortItem("o", 2, self))
        self.loadedFiles = []

        self.changeSize()
        self.addTree()

    def getInternalPiping(self) -> InternalPiping:
        inputPort = _mfn.PortItem("input", _mfn.PortItemType.INPUT)
        outputPort = _mfn.PortItem("output", _mfn.PortItemType.OUTPUT)
        pipe = _mfn.Pipe(self.displayName, self.trnsysId, inputPort, outputPort)

        return InternalPiping([pipe], {inputPort: self.inputs[0], outputPort: self.outputs[0]})

    def _getImageAccessor(self) -> _tp.Optional[_img.ImageAccessor]:
        return _img.PT_FIELD_SVG

    def changeSize(self):
        w = self.w
        h = self.h

        delta = 20

        if h < 20:
            h = 20
        if w < 40:
            w = 40

        rect = self.label.boundingRect()
        lw, lh = rect.width(), rect.height()
        lx = (w - lw) / 2
        self.label.setPos(lx, h)

        self.origInputsPos = [[4*delta, h]]
        self.origOutputsPos = [[4*delta, 0]]

        self.outputs[0].setPos(self.origOutputsPos[0][0], self.origOutputsPos[0][1])
        self.inputs[0].setPos(self.origInputsPos[0][0], self.origInputsPos[0][1])

        self.updateFlipStateH(self.flippedH)
        self.updateFlipStateV(self.flippedV)

        self.inputs[0].side = (self.rotationN + 2 - 2 * self.flippedH) % 4
        self.outputs[0].side = (self.rotationN + 2 - 2 * self.flippedH) % 4

        return w, h

    def addTree(self):
        """
        When a blockitem is added to the main window.
        A file explorer for that item is added to the right of the main window by calling this method
        """
        if self.parent.parent().projectPath == "":
            self.path = self.parent.parent().projectFolder
        else:
            self.path = self.parent.parent().projectPath

        pathName = self.displayName
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

    def hasDdckPlaceHolders(self):
        return True

    def deleteBlock(self):
        """
        Overridden method to also delete folder
        """
        self.logger.debug("Block " + str(self) + " is deleting itself (" + self.displayName + ")")
        self.deleteConns()
        self.parent.parent().trnsysObj.remove(self)
        self.logger.debug("deleting block " + str(self) + self.displayName)
        self.parent.scene().removeItem(self)
        widgetToRemove = self.parent.parent().findChild(QTreeView, self.displayName + "Tree")
        try:
            shutil.rmtree(self.path)
        except:
            pass
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
