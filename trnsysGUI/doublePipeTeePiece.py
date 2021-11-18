# pylint: skip-file

import typing as _tp

import massFlowSolver as _mfs
import massFlowSolver.networkModel as _mfn
import trnsysGUI.images as _img
from massFlowSolver import InternalPiping
from trnsysGUI.modelPortItems import ColdPortItem, HotPortItem
from trnsysGUI.BlockItem import BlockItem  # type: ignore[attr-defined]
from trnsysGUI.DoublePipePortItem import DoublePipePortItem  # type: ignore[attr-defined]
from trnsysGUI.connection.doublePipeConnection import DoublePipeConnection


class DoublePipeTeePiece(BlockItem):
    def __init__(self, trnsysType, parent, **kwargs):
        super().__init__(trnsysType, parent, **kwargs)

        self.w = 60
        self.h = 40

        self.typeNumber = 2

        self.inputs.append(DoublePipePortItem("i", 0, self))
        self.inputs.append(DoublePipePortItem("i", 2, self))
        self.outputs.append(DoublePipePortItem("o", 1, self))

        self.changeSize()

        self.childIds = []
        self.childIds.append(self.trnsysId)
        self.childIds.append(self.parent.parent().idGen.getTrnsysID())

    def _getImageAccessor(self) -> _tp.Optional[_img.ImageAccessor]:
        rotationAngle = (self.rotationN % 4) * 90

        if rotationAngle == 0:
            return _img.DP_TEE_PIECE_SVG

        if rotationAngle == 90:
            return _img.DP_TEE_PIECE_ROTATED_90

        if rotationAngle == 180:
            return _img.DP_TEE_PIECE_ROTATED_180

        if rotationAngle == 270:
            return _img.DP_TEE_PIECE_ROTATED_270

        raise AssertionError("Can't get here.")

    def changeSize(self):
        width, _ = self._getCappedWithAndHeight()
        self._positionLabel()

        self.origInputsPos = [[0, 30], [width, 30]]
        self.origOutputsPos = [[30, 0]]
        self.inputs[0].setPos(self.origInputsPos[0][0], self.origInputsPos[0][1])

        self.inputs[1].setPos(self.origInputsPos[1][0], self.origInputsPos[1][1])
        self.outputs[0].setPos(self.origOutputsPos[0][0], self.origOutputsPos[0][1])

        # pylint: disable=duplicate-code  # 1
        self.updateFlipStateH(self.flippedH)
        self.updateFlipStateV(self.flippedV)

        self.inputs[0].side = (self.rotationN + 2 * self.flippedH) % 4
        self.inputs[1].side = (self.rotationN + 2 - 2 * self.flippedH) % 4
        # pylint: disable=duplicate-code  # 1
        self.outputs[0].side = (self.rotationN + 1 - 1 * self.flippedH) % 4

    def encode(self):
        portListInputs = []
        portListOutputs = []

        for inp in self.inputs:
            portListInputs.append(inp.id)
        for output in self.outputs:
            portListOutputs.append(output.id)

        dct = {}

        dct[".__BlockDict__"] = True
        dct["BlockName"] = self.name
        dct["BlockDisplayName"] = self.displayName
        dct["BlockPosition"] = (float(self.pos().x()), float(self.pos().y()))
        dct["ID"] = self.id
        dct["trnsysID"] = self.trnsysId
        dct["childIds"] = self.childIds
        dct["PortsIDIn"] = portListInputs
        dct["PortsIDOut"] = portListOutputs
        dct["FlippedH"] = self.flippedH
        dct["FlippedV"] = self.flippedV
        dct["RotationN"] = self.rotationN
        dct["GroupName"] = self.groupName

        dictName = "Block-"

        return dictName, dct

    def decode(self, i, resBlockList):
        self.childIds = i["childIds"]
        super().decode(i, resBlockList)

    def _getConnectedRealNode(self, portItem: _mfn.PortItem, internalPiping: _mfs.InternalPiping) \
            -> _tp.Optional[_mfn.RealNodeBase]:
        assert portItem in internalPiping.modelPortItemsToGraphicalPortItem, \
            "`portItem' does not belong to this `BlockItem'."

        graphicalPortItem = internalPiping.modelPortItemsToGraphicalPortItem[portItem]

        if not graphicalPortItem.connectionList:
            return None

        connection: _mfs.MassFlowNetworkContributorMixin = graphicalPortItem.connectionList[0]

        connectionInternalPiping = connection.getInternalPiping()
        connectionStartingNodes = connectionInternalPiping.openLoopsStartingNodes

        assert isinstance(connection, DoublePipeConnection), "Connection is not a doublePipe"
        connectionColdPort = connectionStartingNodes[0]
        connectionHotPort = connectionStartingNodes[1]

        if isinstance(portItem, ColdPortItem):
            return connectionColdPort
        if isinstance(portItem, HotPortItem):
            return connectionHotPort

        return None

    def getInternalPiping(self) -> InternalPiping:
        coldInput1: _mfn.PortItem = ColdPortItem()
        coldInput2: _mfn.PortItem = ColdPortItem()
        coldOutput: _mfn.PortItem = ColdPortItem()
        coldTeePiece = _mfn.TeePiece(self.displayName + "Cold", self.childIds[0], coldInput1, coldInput2, coldOutput)
        coldModelPortItemsToGraphicalPortItem = {
            coldInput1: self.inputs[0], coldInput2: self.inputs[1], coldOutput: self.outputs[0]}

        hotInput1: _mfn.PortItem = HotPortItem()
        hotInput2: _mfn.PortItem = HotPortItem()
        hotOutput: _mfn.PortItem = HotPortItem()
        hotTeePiece = _mfn.TeePiece(self.displayName + "Hot", self.childIds[1], hotInput1, hotInput2, hotOutput)
        hotModelPortItemsToGraphicalPortItem = {
            hotInput1: self.inputs[0], hotInput2: self.inputs[1], hotOutput: self.outputs[0]}

        modelPortItemsToGraphicalPortItem = coldModelPortItemsToGraphicalPortItem | hotModelPortItemsToGraphicalPortItem

        internalPiping = InternalPiping([coldTeePiece, hotTeePiece], modelPortItemsToGraphicalPortItem)

        return internalPiping

    def exportPipeAndTeeTypesForTemp(self, startingUnit): # pylint: disable=too-many-locals
        unitNumber = startingUnit
        tNr = 929  # Temperature calculation from a tee-piece

        unitText = ""
        ambientT = 20

        equationConstant = 1

        openLoops, nodesToIndices = self._getOpenLoopsAndNodeToIndices()
        assert len(openLoops) == 2
        temps = ["Cold", "Hot"]

        for openLoop, temp in zip(openLoops, temps):
            unitText += "UNIT " + str(unitNumber) + " TYPE " + str(tNr) + "\n"
            unitText += "!" + self.displayName + temp + "\n"
            unitText += "PARAMETERS 0\n"
            unitText += "INPUTS 6\n"

            realNodes = [n for n in openLoop.nodes if isinstance(n, _mfn.RealNodeBase)]
            assert len(realNodes) == 1
            realNode = realNodes[0]

            outputVariables = realNode.serialize(nodesToIndices).outputVariables
            for outputVariable in outputVariables:
                if not outputVariable:
                    continue

                unitText += outputVariable.name + "\n"

            unitText += f"T{self.inputs[0].connectionList[0].displayName}{temp}\n"
            unitText += f"T{self.inputs[1].connectionList[0].displayName}{temp}\n"
            unitText += f"T{self.outputs[0].connectionList[0].displayName}{temp}\n"

            unitText += "***Initial values\n"
            unitText += 3 * "0 " + 3 * (str(ambientT) + " ") + "\n"

            unitText += "EQUATIONS 1\n"
            unitText += "T" + self.displayName + temp + "= [" + str(unitNumber) + "," + str(equationConstant) + "]\n\n"

            unitNumber += 1

        return unitText, unitNumber
