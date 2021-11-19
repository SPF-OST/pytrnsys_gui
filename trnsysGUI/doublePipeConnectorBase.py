
import typing as _tp

import massFlowSolver as _mfs
import massFlowSolver.networkModel as _mfn
import trnsysGUI.images as _img
from massFlowSolver import InternalPiping
from trnsysGUI.modelPortItems import ColdPortItem, HotPortItem
from trnsysGUI.BlockItem import BlockItem  # type: ignore[attr-defined]
from trnsysGUI.connection.doublePipeConnection import DoublePipeConnection
from trnsysGUI.connection.singlePipeConnection import SinglePipeConnection  # type: ignore[attr-defined]


class DoublePipeConnectorBase(BlockItem):
    def __init__(self, trnsysType, parent, **kwargs):
        super().__init__(trnsysType, parent, **kwargs)

        self.w = 20
        self.h = 20

        self.childIds = []
        self.childIds.append(self.trnsysId)
        self.childIds.append(self.parent.parent().idGen.getTrnsysID())

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
        super().decode(i, resBlockList)
        self.childIds = i["childIds"]

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

        if isinstance(connection, SinglePipeConnection):
            connectionSinglePort = connectionStartingNodes[0]
            return connectionSinglePort

        if isinstance(connection, DoublePipeConnection):
            connectionColdPort = connectionStartingNodes[0]
            connectionHotPort = connectionStartingNodes[1]

            if isinstance(portItem, ColdPortItem):
                return connectionColdPort
            if isinstance(portItem, HotPortItem):
                return connectionHotPort

            raise AssertionError("PortItem has not a doublePipePortItem.")

        raise AssertionError("Connection is an unknown class.")

    def getInternalPiping(self) -> InternalPiping:
        raise NotImplementedError

    def exportPipeAndTeeTypesForTemp(self, startingUnit):
        raise NotImplementedError

    def _getEquations(self, inp, temperature):
        unitText = "!" + self.displayName + temperature + "\n"
        unitText += "EQUATIONS 1\n"

        tIn = f"GT(Mfr{self.displayName}{temperature}_A, 0)*T{inp.connectionList[0].displayName} + " \
              f"LT(Mfr{self.displayName}{temperature}_A, 0)*" \
              f"T{self.outputs[0].connectionList[0].displayName}{temperature}"
        tOut = f"T{self.displayName}{temperature}"  # pylint: disable=duplicate-code
        unitText += f"{tOut} = {tIn}\n\n"
        return unitText
