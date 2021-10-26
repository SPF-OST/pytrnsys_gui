# pylint: skip-file
# type: ignore

import os
import pathlib as _pl
import shutil
import typing as _tp

from PyQt5.QtWidgets import QMenu, QFileDialog, QTreeView

import massFlowSolver.networkModel as _mfn
import trnsysGUI.images as _img
from trnsysGUI.BlockItem import BlockItem
from massFlowSolver import InternalPiping
from trnsysGUI.MyQFileSystemModel import MyQFileSystemModel
from trnsysGUI.MyQTreeView import MyQTreeView
from trnsysGUI.SinglePipePortItem import SinglePipePortItem


class GenericBlock(BlockItem):
    def __init__(self, trnsysType, parent, **kwargs):
        super(GenericBlock, self).__init__(trnsysType, parent, **kwargs)

        self.inputs.append(SinglePipePortItem("i", 2, self))
        self.outputs.append(SinglePipePortItem("o", 2, self))
        self.loadedFiles = []

        self.childIds = []
        self.childIds.append(self.trnsysId)

        self._imageAccessor = _img.GENERIC_BLOCK_PNG

        # Disallow adding port pairs later, because the trnsysIDs of the generated port pairs have to be
        # consecutive to be correctly printed out in the export
        self.isSet = True

        self.changeSize()
        self.addTree()

    def _getImageAccessor(self) -> _tp.Optional[_img.ImageAccessor]:
        return _img.GENERIC_BLOCK_PNG

    def changeSize(self):
        w = self.w
        h = self.h
        delta = 4

        """ Resize block function """

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

        self.outputs[0].setPos(2 * delta + w, h - 2 * delta)
        self.inputs[0].setPos(2 * delta + w, 2 * delta)

        return w, h

    def getPairNb(self, side):
        res = 0
        for i in self.inputs:
            if i.side == side:
                res += 1

        self.logger.debug("there are " + str(res) + " pairs on the side " + str(side))
        return res

    def addPortDlg(self):
        self.parent.parent().showGenericPortPairDlg(self)

    def addPort(self, io, relH):
        self.logger.debug(io)
        self.logger.debug(relH)

    def setImage(self):
        pixmap = self._getPixmap()
        self.setPixmap(pixmap)

    def changeImage(self):
        name = str(self.pickImage().resolve())
        if name[-3:] == "png" or name[-3:] == "svg":
            self.setImageSource(name)
            self.setImage()
        else:
            self.logger.debug("No image picked, name is " + name)

    def setImageSource(self, name):
        self._imageAccessor = _img.ImageAccessor.createForFile(_pl.Path(name))

    def pickImage(self):
        return _pl.Path(QFileDialog.getOpenFileName(self.parent.parent(), filter="*.png *.svg")[0])

    def contextMenuEvent(self, event):
        menu = QMenu()

        a1 = menu.addAction("Launch NotePad++")
        a1.triggered.connect(self.launchNotepadFile)

        rr = _img.ROTATE_TO_RIGHT_PNG.icon()
        a2 = menu.addAction(rr, "Rotate Block clockwise")
        a2.triggered.connect(self.rotateBlockCW)

        ll = _img.ROTATE_LEFT_PNG.icon()
        a3 = menu.addAction(ll, "Rotate Block counter-clockwise")
        a3.triggered.connect(self.rotateBlockCCW)

        a4 = menu.addAction("Reset Rotation")
        a4.triggered.connect(self.resetRotation)

        b1 = menu.addAction("Print Rotation")
        b1.triggered.connect(self.printRotation)

        c1 = menu.addAction("Delete this Block")
        c1.triggered.connect(self.deleteBlock)

        c3 = menu.addAction("Set image")
        c3.triggered.connect(self.changeImage)

        if not self.isSet:
            c4 = menu.addAction("Add port")
            c4.triggered.connect(self.addPortDlg)

        menu.exec_(event.screenPos())

    def encode(self):
        if self.isVisible():
            self.logger.debug("Encoding a Generic Block")

            portListInputs = []
            portListOutputs = []

            for p in self.inputs:
                portListInputs.append(p.id)
            for p in self.outputs:
                portListOutputs.append(p.id)

            dct = {}
            dct[".__BlockDict__"] = True
            dct["BlockName"] = self.name
            dct["BlockDisplayName"] = self.displayName
            dct["BlockPosition"] = (float(self.pos().x()), float(self.pos().y()))
            dct["ID"] = self.id
            dct["trnsysID"] = self.trnsysId
            dct["PortsIDIn"] = portListInputs
            dct["PortsIDOut"] = portListOutputs
            dct["FlippedH"] = self.flippedH
            dct["FlippedV"] = self.flippedV
            dct["RotationN"] = self.rotationN
            dct["GroupName"] = self.groupName
            dct["Imagesource"] = self._imageAccessor.getResourcePath()
            dct["PortPairsNb"] = [self.getPairNb(i) for i in range(4)]

            dictName = "Block-"
            return dictName, dct

    def decode(self, i, resBlockList):
        assert len(self.inputs) == len(self.outputs)
        numberOfPortPairs = len(self.inputs)
        for portPairIndex in range(numberOfPortPairs):
            self.removePortPair(portPairIndex)

        numberOfPortPairsBySide = i["PortPairsNb"]
        for side in range(3):
            numberOfPortPairsToAdd = numberOfPortPairsBySide[side]
            for _ in range(numberOfPortPairsToAdd):
                self.addPortPair(side)

        super(GenericBlock, self).decode(i, resBlockList)
        self._imageAccessor = _img.ImageAccessor.createFromResourcePath(i["Imagesource"])
        self.setImage()

    def decodePaste(self, i, offset_x, offset_y, resConnList, resBlockList, **kwargs):
        correcter = 0
        for j in range(4):
            if j == 2:
                correcter = -1
            for k in range(i["PortPairsNb"][j] + correcter):
                self.addPortPair(j)

        super(GenericBlock, self).decodePaste(i, offset_x, offset_y, resConnList, resBlockList)
        self._imageAccessor = _img.ImageAccessor.createFromResourcePath(i["Imagesource"])
        self.setImage()

    def addPortPair(self, side):
        h = self.h
        w = self.w
        delta = 4
        self.logger.debug("side is " + str(side))
        self.inputs.append(SinglePipePortItem("i", side, self))
        self.outputs.append(SinglePipePortItem("o", side, self))
        # Allocate id
        self.childIds.append(self.parent.parent().idGen.getTrnsysID())

        portNb = [0, 0, 0, 0]
        for i in self.inputs:
            if i.side == 0:
                distBetweenPorts = (self.h - 4 * delta) / (2 * self.getPairNb(0) - 1)
                self.logger.debug("distance betw ports " + str(distBetweenPorts))
                i.setPos(-2 * delta, 2 * delta + distBetweenPorts * portNb[0])
                portNb[0] += 1

                self.outputs[self.inputs.index(i)].setPos(-2 * delta, 2 * delta + distBetweenPorts * portNb[0])
                portNb[0] += 1
            elif i.side == 1:
                distBetweenPorts = (self.w - 4 * delta) / (2 * self.getPairNb(1) - 1)
                i.setPos(2 * delta + distBetweenPorts * portNb[1], -2 * delta)
                portNb[1] += 1

                self.outputs[self.inputs.index(i)].setPos(2 * delta + distBetweenPorts * portNb[1], -2 * delta)
                portNb[1] += 1

            elif i.side == 2:
                self.logger.debug("side == 2")
                distBetweenPorts = (self.h - 4 * delta) / (2 * self.getPairNb(2) - 1)
                self.logger.debug("side 2 dist betw ports is " + str(distBetweenPorts))
                i.setPos(2 * delta + w, 2 * delta + distBetweenPorts * portNb[2])
                self.logger.debug(2 * delta + distBetweenPorts * portNb[2])
                portNb[2] += 1

                self.outputs[self.inputs.index(i)].setPos(2 * delta + w, 2 * delta + distBetweenPorts * portNb[2])
                self.logger.debug(2 * delta + distBetweenPorts * portNb[2])
                portNb[2] += 1

            else:
                distBetweenPorts = (self.w - 4 * delta) / (2 * self.getPairNb(3) - 1)
                self.logger.debug("distance betw ports " + str(distBetweenPorts))
                i.setPos(2 * delta + distBetweenPorts * portNb[3], 2 * delta + h)
                portNb[3] += 1

                self.outputs[self.inputs.index(i)].setPos(2 * delta + distBetweenPorts * portNb[3], 2 * delta + h)
                portNb[3] += 1

    def removePortPairOnSide(self, side):
        for i in self.inputs:
            if i.side == side:
                self.removePortPair(self.inputs.index(i))
                return

    def removePortPair(self, n):
        self.inputs.remove(self.inputs[n])
        self.outputs.remove(self.outputs[n])

    def updateFlipStateH(self, state):
        self.flippedH = bool(state)

        pixmap = self._getPixmap()
        self.setPixmap(pixmap)

    def updateFlipStateV(self, state):
        self.flippedV = bool(state)

        pixmap = self._getPixmap()
        self.setPixmap(pixmap)

    def getInternalPiping(self) -> InternalPiping:
        assert len(self.inputs) == len(self.outputs)

        pipes = []
        portItems = {}
        for i, (graphicalInputPort, graphicalOutputPort) in enumerate(zip(self.inputs, self.outputs)):
            inputPort = _mfn.PortItem()
            outputPort = _mfn.PortItem()
            pipe = _mfn.Pipe(f"{self.displayName}X{i}", self.childIds[0], inputPort, outputPort)

            pipes.append(pipe)
            portItems[inputPort] = graphicalInputPort
            portItems[outputPort] = graphicalOutputPort

        return InternalPiping(pipes, portItems)

    def getSubBlockOffset(self, c):
        for i in range(len(self.inputs)):
            if (
                self.inputs[i] == c.toPort
                or self.inputs[i] == c.fromPort
                or self.outputs[i] == c.toPort
                or self.outputs[i] == c.fromPort
            ):
                return i

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

    def updateTreePath(self, path):
        """
        When the user chooses the project path for the file explorers, this method is called
        to update the root path.
        """
        pathName = self.displayName
        self.path = os.path.join(path, "ddck")
        self.path = os.path.join(self.path, pathName)
        if not os.path.exists(self.path):
            os.makedirs(self.path)
        self.model.setRootPath(self.path)
        self.tree.setRootIndex(self.model.index(self.path))

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
        shutil.rmtree(self.path)
        self.deleteLoadedFile()
        try:
            widgetToRemove.hide()
        except AttributeError:
            self.logger.debug("Widget doesnt exist!")
        else:
            self.logger.debug("Deleted widget")
        del self

    def setName(self, newName):
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
