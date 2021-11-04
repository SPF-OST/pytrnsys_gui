import typing as _tp

import massFlowSolver as _mfs
import massFlowSolver.networkModel as _mfn
import trnsysGUI.images as _img
from massFlowSolver import InternalPiping
from trnsysGUI.BlockItem import BlockItem  # type: ignore[attr-defined]
from trnsysGUI.DoublePipePortItem import DoublePipePortItem  # type: ignore[attr-defined]


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

    def _getConnectedRealNode(self, portItem: _mfn.PortItem, internalPiping: _mfs.InternalPiping) -> _tp.Optional[_mfn.RealNodeBase]:
        assert portItem in internalPiping.modelPortItemsToGraphicalPortItem, "`portItem' does not belong to this `BlockItem'."

        graphicalPortItem = internalPiping.modelPortItemsToGraphicalPortItem[portItem]

        if not graphicalPortItem.connectionList:
            return None

        connection: _mfs.MassFlowNetworkContributorMixin = graphicalPortItem.connectionList[0]

        connectionInternalPiping = connection.getInternalPiping()

        connectionStartingNodes = connectionInternalPiping.openLoopsStartingNodes

        assert len(connectionStartingNodes) == 2

        if isinstance(portItem, _mfn.ColdPortItem):
            return connectionStartingNodes[0]
        if isinstance(portItem, _mfn.HotPortItem):
            return connectionStartingNodes[1]

        return None

    def getInternalPiping(self) -> InternalPiping:
        coldInput1 = _mfn.ColdPortItem()
        coldInput2 = _mfn.ColdPortItem()
        coldOutput = _mfn.ColdPortItem()
        coldTeePiece = _mfn.TeePiece("Cold"+self.displayName, self.trnsysId, coldInput1, coldInput2, coldOutput)
        ColdModelPortItemsToGraphicalPortItem = {coldInput1: self.inputs[0], coldInput2: self.inputs[1], coldOutput: self.outputs[0]}

        hotInput1 = _mfn.HotPortItem()
        hotInput2 = _mfn.HotPortItem()
        hotOutput = _mfn.HotPortItem()
        hotTeePiece = _mfn.TeePiece("Hot"+self.displayName, self.trnsysId, hotInput1, hotInput2, hotOutput)
        HotModelPortItemsToGraphicalPortItem = {hotInput1: self.inputs[0], hotInput2: self.inputs[1], hotOutput: self.outputs[0]}

        ModelPortItemsToGraphicalPortItem = ColdModelPortItemsToGraphicalPortItem | HotModelPortItemsToGraphicalPortItem

        internalPiping = InternalPiping([coldTeePiece, hotTeePiece], ModelPortItemsToGraphicalPortItem)

        return internalPiping

    def exportPipeAndTeeTypesForTemp(self, startingUnit):
        raise NotImplementedError()
