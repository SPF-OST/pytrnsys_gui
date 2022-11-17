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


class HPDual(BlockItem, _ip.HasInternalPiping):
    def __init__(self, trnsysType, parent, **kwargs):
        super(HPDual, self).__init__(trnsysType, parent, **kwargs)

        self.inputs.append(_cspi.createSinglePipePortItem("i", 0, self))
        self.inputs.append(_cspi.createSinglePipePortItem("i", 2, self))

        self.outputs.append(_cspi.createSinglePipePortItem("o", 0, self))
        self.outputs.append(_cspi.createSinglePipePortItem("o", 2, self))

        self.loadedFiles = []

        # For restoring correct order of trnsysObj list
        self.childIds = []
        self.childIds.append(self.trnsysId)
        self.childIds.append(self.parent.parent().idGen.getTrnsysID())

        self.changeSize()
        self.addTree()

    def getDisplayName(self) -> str:
        return self.displayName

    def _getImageAccessor(self) -> _tp.Optional[_img.ImageAccessor]:
        return _img.HP_DUAL_SVG

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

        self.origInputsPos = [[0, h - 2 * delta], [w, h - delta]]  # inlet of [evap, cond]
        self.origOutputsPos = [[0, h - delta], [w, delta]]  # outlet of [evap, cond]

        self.inputs[0].setPos(self.origInputsPos[0][0], self.origInputsPos[0][1])  # evap
        self.inputs[1].setPos(self.origInputsPos[1][0], self.origInputsPos[0][1])  # cond

        self.outputs[0].setPos(self.origOutputsPos[0][0], self.origOutputsPos[0][1])
        self.outputs[1].setPos(self.origOutputsPos[1][0], self.origOutputsPos[1][1])

        self.updateFlipStateH(self.flippedH)
        self.updateFlipStateV(self.flippedV)

        self.inputs[0].side = (self.rotationN + 2 * self.flippedH) % 4
        self.inputs[1].side = (self.rotationN + 2 - 2 * self.flippedH) % 4

        self.outputs[0].side = (self.rotationN + 2 * self.flippedH) % 4
        self.outputs[1].side = (self.rotationN + 2 - 2 * self.flippedH) % 4

        return w, h

    def encode(self):
        if self.isVisible():
            self.logger.debug("Encoding a HeatPumpDual")

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
            dct["PortsIDIn"] = portListInputs
            dct["PortsIDOut"] = portListOutputs
            dct["HeatPumpPosition"] = (float(self.pos().x()), float(self.pos().y()))
            dct["ID"] = self.id
            dct["trnsysID"] = self.trnsysId
            dct["childIds"] = self.childIds
            dct["FlippedH"] = self.flippedH
            dct["FlippedV"] = self.flippedH
            dct["RotationN"] = self.rotationN

            dictName = "Block-"

            return dictName, dct

    def decode(self, i, resBlockList):
        self.flippedH = i["FlippedH"]
        self.flippedV = i["FlippedV"]
        self.childIds = i["childIds"]
        self.displayName = i["BlockDisplayName"]
        self.changeSize()

        for x in range(len(self.inputs)):
            self.inputs[x].id = i["PortsIDIn"][x]
            self.logger.debug("Input at heatExchanger")

        for x in range(len(self.outputs)):
            self.outputs[x].id = i["PortsIDOut"][x]
            self.logger.debug("Output at heatExchanger")

        self.setPos(float(i["HeatPumpPosition"][0]), float(i["HeatPumpPosition"][1]))
        self.trnsysId = i["trnsysID"]
        self.id = i["ID"]

        resBlockList.append(self)

    def decodePaste(self, i, offset_x, offset_y, resConnList, resBlockList, **kwargs):
        self.flippedH = i["FlippedH"]
        self.flippedV = i["FlippedV"]

        self.changeSize()

        for x in range(len(self.inputs)):
            self.inputs[x].id = i["PortsIDIn"][x]
            self.logger.debug("Input at heatExchanger")

        for x in range(len(self.outputs)):
            self.outputs[x].id = i["PortsIDOut"][x]
            self.logger.debug("Output at heatExchanger")

        self.setPos(float(i["HeatPumpPosition"][0] + offset_x), float(i["HeatPumpPosition"][1] + offset_y))

        resBlockList.append(self)

    def getInternalPiping(self) -> _ip.InternalPiping:
        condenserInput = _mfn.PortItem("In", _mfn.PortItemDirection.INPUT)
        condenserOutput = _mfn.PortItem("Out", _mfn.PortItemDirection.OUTPUT)
        condenserPipe = _mfn.Pipe(condenserInput, condenserOutput, "Cond")

        evaporatorInput = _mfn.PortItem("In", _mfn.PortItemDirection.INPUT)
        evaporatorOutput = _mfn.PortItem("Out", _mfn.PortItemDirection.OUTPUT)
        evaporatorPipe = _mfn.Pipe(evaporatorInput, evaporatorOutput, "Evap")

        modelPortItemsToGraphicalPortItem = {
            condenserInput: self.inputs[1],
            condenserOutput: self.outputs[1],
            evaporatorInput: self.inputs[0],
            evaporatorOutput: self.outputs[0],
        }
        nodes = [condenserPipe, evaporatorPipe]

        return _ip.InternalPiping(nodes, modelPortItemsToGraphicalPortItem)

    def getSubBlockOffset(self, c):
        for i in range(3):
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
        # self.logger.debug("self.parent.parent" + str(self.parent.parent()))
        self.parent.parent().trnsysObj.remove(self)
        self.logger.debug("deleting block " + str(self) + self.displayName)
        # self.logger.debug("self.scene is" + str(self.parent.scene()))
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
        # destPath = str(os.path.dirname(self.path))+'\\HPTwoHx_'+self.displayName
        destPath = os.path.join(os.path.split(self.path)[0], self.displayName)
        if os.path.exists(self.path):
            os.rename(self.path, destPath)
            self.path = destPath
            self.logger.debug(self.path)
