import os
import typing as _tp

import massFlowSolver.networkModel as _mfn
import trnsysGUI.images as _img
from massFlowSolver import InternalPiping
from massFlowSolver.modelPortItems import ColdPortItem, HotPortItem
from trnsysGUI.DoublePipePortItem import DoublePipePortItem  # type: ignore[attr-defined]
from trnsysGUI.MyQFileSystemModel import MyQFileSystemModel
from trnsysGUI.MyQTreeView import MyQTreeView
from trnsysGUI.doublePipeConnectorBase import DoublePipeConnectorBase


class DoubleDoublePipeConnector(DoublePipeConnectorBase):
    def __init__(self, trnsysType, parent, **kwargs):
        super().__init__(trnsysType, parent, **kwargs)

        self.inputs.append(DoublePipePortItem("i", 0, self))
        self.outputs.append(DoublePipePortItem("o", 2, self))

        self.changeSize()
        self.addTree()

        self.childIds = []
        self.childIds.append(self.trnsysId)
        self.childIds.append(self.parent.parent().idGen.getTrnsysID())

    def _getImageAccessor(self) -> _tp.Optional[_img.ImageAccessor]:
        return _img.DOUBLE_DOUBLE_PIPE_CONNECTOR_SVG

    def changeSize(self):
        super().changeSize()

        self.origInputsPos = [[0, 10]]
        self.origOutputsPos = [[20, 10]]

        self.inputs[0].setPos(self.origInputsPos[0][0], self.origInputsPos[0][1])
        self.outputs[0].setPos(self.origOutputsPos[0][0], self.origOutputsPos[0][1])

        # pylint: disable=duplicate-code  # 3
        self.updateFlipStateH(self.flippedH)
        self.updateFlipStateV(self.flippedV)

        self.inputs[0].side = (self.rotationN + 2 * self.flippedH) % 4
        self.outputs[0].side = (self.rotationN + 2 - 2 * self.flippedH) % 4

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

    def getInternalPiping(self) -> InternalPiping:
        coldInput = ColdPortItem()
        coldOutput = ColdPortItem()
        coldTeePiece = _mfn.Pipe(self.displayName + "Cold", self.childIds[0], coldInput, coldOutput)
        ColdModelPortItemsToGraphicalPortItem = {coldInput: self.inputs[0], coldOutput: self.outputs[0]}

        hotInput = HotPortItem()
        hotOutput = HotPortItem()
        hotTeePiece = _mfn.Pipe(self.displayName + "Hot", self.childIds[1], hotInput, hotOutput)
        HotModelPortItemsToGraphicalPortItem = {hotInput: self.inputs[0], hotOutput: self.outputs[0]}

        ModelPortItemsToGraphicalPortItem = ColdModelPortItemsToGraphicalPortItem | HotModelPortItemsToGraphicalPortItem

        internalPiping = InternalPiping([coldTeePiece, hotTeePiece], ModelPortItemsToGraphicalPortItem)

        return internalPiping

    def exportPipeAndTeeTypesForTemp(self, startingUnit):
        if self.isVisible():
            unitNumber = startingUnit

            unitText = ""

            openLoops, nodesToIndices = self._getOpenLoopsAndNodeToIndices()
            assert len(openLoops) == 2
            temps = ["Cold", "Hot"]

            for openLoop, temp in zip(openLoops, temps):
                # unitText += "UNIT " + str(unitNumber) + "\n"
                unitText += "!" + self.displayName + temp + "\n\n"

                unitText += "EQUATIONS 1\n"

                tIn = f"GT(Mfr{self.displayName}{temp}_A, 0)*T{self.inputs[0].connectionList[0].displayName}{temp} + " \
                      f"LT(Mfr{self.displayName}{temp}_A, 0)*T{self.outputs[0].connectionList[0].displayName}{temp}"
                tOut = f"T{self.displayName}{temp}"
                unitText += f"{tOut} = {tIn}\n\n"

                unitNumber += 1

            return unitText, unitNumber
        else:
            return "", startingUnit
