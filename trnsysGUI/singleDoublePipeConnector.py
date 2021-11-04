import typing as _tp

import massFlowSolver as _mfs
import massFlowSolver.networkModel as _mfn
import trnsysGUI.images as _img
from massFlowSolver import InternalPiping
from trnsysGUI.doublePipeConnectorBase import DoublePipeConnectorBase
from trnsysGUI.DoublePipePortItem import DoublePipePortItem  # type: ignore[attr-defined]
from trnsysGUI.SinglePipePortItem import SinglePipePortItem  # type: ignore[attr-defined]


class SingleDoublePipeConnector(DoublePipeConnectorBase):
    def __init__(self, trnsysType, parent, **kwargs):
        super().__init__(trnsysType, parent, **kwargs)

        self.inputs.append(SinglePipePortItem("i", 0, self))
        self.inputs.append(SinglePipePortItem("i", 0, self))
        self.outputs.append(DoublePipePortItem("o", 2, self))

        self.changeSize()

        self.childIds = []
        self.childIds.append(self.trnsysId)
        self.childIds.append(self.parent.parent().idGen.getTrnsysID())

    def _getImageAccessor(self) -> _tp.Optional[_img.ImageAccessor]:
        return _img.SINGLE_DOUBLE_PIPE_CONNECTOR_SVG

    def changeSize(self):
        super().changeSize()

        self.origInputsPos = [[0, 0], [0, 20]]
        self.origOutputsPos = [[20, 10]]

        self.inputs[0].setPos(self.origInputsPos[0][0], self.origInputsPos[0][1])
        self.inputs[1].setPos(self.origInputsPos[1][0], self.origInputsPos[1][1])
        self.outputs[0].setPos(self.origOutputsPos[0][0], self.origOutputsPos[0][1])

        # pylint: disable=duplicate-code  # 2
        self.updateFlipStateH(self.flippedH)
        self.updateFlipStateV(self.flippedV)

        self.inputs[0].side = (self.rotationN + 2 * self.flippedH) % 4
        self.inputs[1].side = (self.rotationN + 2 * self.flippedH) % 4
        # pylint: disable=duplicate-code  # 2
        self.outputs[0].side = (self.rotationN + 2 - 2 * self.flippedH) % 4

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

        if isinstance(portItem, _mfn.ColdPortItem):
            return connectionStartingNodes[0]
        elif isinstance(portItem, _mfn.HotPortItem):
            return connectionStartingNodes[1]
        else:  # connected on a singlePort-side
            return connectionStartingNodes[0]

    def getInternalPiping(self) -> InternalPiping:
        coldInput1 = _mfn.PortItem()
        coldOutput = _mfn.ColdPortItem()
        coldConnector = _mfn.Pipe("Cold"+self.displayName, self.childIds[0], coldInput1, coldOutput)
        ColdModelPortItemsToGraphicalPortItem = {coldInput1: self.inputs[0], coldOutput: self.outputs[0]}

        hotInput1 = _mfn.PortItem()
        hotOutput = _mfn.HotPortItem()
        hotConnector = _mfn.Pipe("Hot"+self.displayName, self.childIds[1], hotInput1, hotOutput)
        HotModelPortItemsToGraphicalPortItem = {hotInput1: self.inputs[1], hotOutput: self.outputs[0]}

        ModelPortItemsToGraphicalPortItem = ColdModelPortItemsToGraphicalPortItem | HotModelPortItemsToGraphicalPortItem

        internalPiping = InternalPiping([coldConnector, hotConnector], ModelPortItemsToGraphicalPortItem)

        return internalPiping

    def exportPipeAndTeeTypesForTemp(self, startingUnit):
        raise NotImplementedError()
