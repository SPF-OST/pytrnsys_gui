
import typing as _tp

import massFlowSolver as _mfs
import massFlowSolver.networkModel as _mfn
import trnsysGUI.images as _img
from massFlowSolver import InternalPiping
from massFlowSolver.modelPortItems import ColdPortItem, HotPortItem
from trnsysGUI.DoublePipePortItem import DoublePipePortItem  # type: ignore[attr-defined]
from trnsysGUI.doublePipeConnectorBase import DoublePipeConnectorBase


class DoubleDoublePipeConnector(DoublePipeConnectorBase):
    def __init__(self, trnsysType, parent, **kwargs):
        super().__init__(trnsysType, parent, **kwargs)

        self.inputs.append(DoublePipePortItem("i", 0, self))
        self.outputs.append(DoublePipePortItem("o", 2, self))

        self.changeSize()

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
        # pylint: disable=duplicate-code  # 3

    def encode(self):
        # Double check that no virtual block gets encoded
        if self.isVisible():
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

    def _getConnectedRealNode(self, portItem: _mfn.PortItem, internalPiping: _mfs.InternalPiping) -> _tp.Optional[_mfn.RealNodeBase]:
        assert portItem in internalPiping.modelPortItemsToGraphicalPortItem, "`portItem' does not belong to this `BlockItem'."

        graphicalPortItem = internalPiping.modelPortItemsToGraphicalPortItem[portItem]

        if not graphicalPortItem.connectionList:
            return None

        connection: _mfs.MassFlowNetworkContributorMixin = graphicalPortItem.connectionList[0]

        connectionInternalPiping = connection.getInternalPiping()
        connectionStartingNodes = connectionInternalPiping.openLoopsStartingNodes

        assert len(connectionStartingNodes) == 2, "Connection is not a doublePipe"
        connectionColdPort = connectionStartingNodes[0]
        connectionHotPort = connectionStartingNodes[1]

        if isinstance(portItem, ColdPortItem):
            return connectionColdPort
        if isinstance(portItem, HotPortItem):
            return connectionHotPort

        return None

    def getInternalPiping(self) -> InternalPiping:
        coldInput = ColdPortItem()
        coldOutput = ColdPortItem()
        coldTeePiece = _mfn.Pipe("Cold"+self.displayName, self.childIds[0], coldInput, coldOutput)
        ColdModelPortItemsToGraphicalPortItem = {coldInput: self.inputs[0], coldOutput: self.outputs[0]}

        hotInput = HotPortItem()
        hotOutput = HotPortItem()
        hotTeePiece = _mfn.Pipe("Hot"+self.displayName, self.childIds[1], hotInput, hotOutput)
        HotModelPortItemsToGraphicalPortItem = {hotInput: self.inputs[0], hotOutput: self.outputs[0]}

        ModelPortItemsToGraphicalPortItem = ColdModelPortItemsToGraphicalPortItem | HotModelPortItemsToGraphicalPortItem

        internalPiping = InternalPiping([coldTeePiece, hotTeePiece], ModelPortItemsToGraphicalPortItem)

        return internalPiping

    def exportPipeAndTeeTypesForTemp(self, startingUnit):
        raise NotImplementedError()
