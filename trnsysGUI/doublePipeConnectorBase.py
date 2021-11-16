
import typing as _tp

import massFlowSolver as _mfs
import massFlowSolver.networkModel as _mfn
import trnsysGUI.images as _img
from massFlowSolver import InternalPiping
from massFlowSolver.modelPortItems import ColdPortItem, HotPortItem
from trnsysGUI.BlockItem import BlockItem  # type: ignore[attr-defined]
from trnsysGUI.connection.doublePipeConnection import DoublePipeConnection
from trnsysGUI.connection.singlePipeConnection import SinglePipeConnection


class DoublePipeConnectorBase(BlockItem):
    def __init__(self, trnsysType, parent, **kwargs):
        super().__init__(trnsysType, parent, **kwargs)

        self.w = 20
        self.h = 20

    def _getImageAccessor(self) -> _tp.Optional[_img.ImageAccessor]:
        raise NotImplementedError()

    def rotateBlockCW(self):
        super().rotateBlockCW()
        self._flipPipes()

    def rotateBlockCCW(self):
        super().rotateBlockCCW()
        self._flipPipes()

    def _flipPipes(self):
        angle = (self.rotationN % 4) * 90
        if angle == 0:
            self.updateFlipStateV(False)
        elif angle == 90:
            self.updateFlipStateV(True)
        elif angle == 180:
            self.updateFlipStateV(True)
        elif angle == 270:
            self.updateFlipStateV(False)

    def resetRotation(self):
        super().resetRotation()
        self.updateFlipStateV(0)

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

        if isinstance(connection, SinglePipeConnection):
            connectionSinglePort = connectionStartingNodes[0]
            return connectionSinglePort

        elif isinstance(connection, DoublePipeConnection):
            connectionColdPort = connectionStartingNodes[0]
            connectionHotPort = connectionStartingNodes[1]

            if isinstance(portItem, ColdPortItem):
                return connectionColdPort
            elif isinstance(portItem, HotPortItem):
                return connectionHotPort
            else:
                raise AssertionError("PortItem has not a doublePipePortItem.")

        else:
            raise AssertionError("Connection is an unknown class.")

    def getInternalPiping(self) -> InternalPiping:
        raise NotImplementedError

    def exportPipeAndTeeTypesForTemp(self, startingUnit):
        raise NotImplementedError

