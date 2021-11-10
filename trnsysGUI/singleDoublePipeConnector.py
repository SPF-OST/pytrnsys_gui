import typing as _tp

import massFlowSolver as _mfs
import massFlowSolver.networkModel as _mfn
import trnsysGUI.images as _img
from massFlowSolver import InternalPiping
from massFlowSolver.modelPortItems import ColdPortItem, HotPortItem
from trnsysGUI.DoublePipePortItem import DoublePipePortItem  # type: ignore[attr-defined]
from trnsysGUI.SinglePipePortItem import SinglePipePortItem  # type: ignore[attr-defined]
from trnsysGUI.doublePipeConnectorBase import DoublePipeConnectorBase
from trnsysGUI.connection.singlePipeConnection import SinglePipeConnection
from trnsysGUI.connection.doublePipeConnection import DoublePipeConnection


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
        coldInput1 = ColdPortItem()
        coldOutput = ColdPortItem()
        coldConnector = _mfn.Pipe(self.displayName + "Cold", self.childIds[0], coldInput1, coldOutput)
        ColdModelPortItemsToGraphicalPortItem = {coldInput1: self.inputs[0], coldOutput: self.outputs[0]}

        hotInput1 = HotPortItem()
        hotOutput = HotPortItem()
        hotConnector = _mfn.Pipe(self.displayName + "Hot", self.childIds[1], hotInput1, hotOutput)
        HotModelPortItemsToGraphicalPortItem = {hotInput1: self.inputs[1], hotOutput: self.outputs[0]}

        ModelPortItemsToGraphicalPortItem = ColdModelPortItemsToGraphicalPortItem | HotModelPortItemsToGraphicalPortItem

        internalPiping = InternalPiping([coldConnector, hotConnector], ModelPortItemsToGraphicalPortItem)

        return internalPiping

    def exportPipeAndTeeTypesForTemp(self, startingUnit):
        if self.isVisible():
            f = ""
            unitNumber = startingUnit
            tNr = 929  # Temperature calculation from a tee-piece

            unitText = ""
            ambientT = 20

            equationConstant = 1

            unitText += "UNIT " + str(unitNumber) + " TYPE " + str(tNr) + "\n"
            unitText += "!" + self.displayName + "\n"
            unitText += "PARAMETERS 0\n"
            unitText += "INPUTS 6\n"

            openLoops, nodesToIndices = self._getOpenLoopsAndNodeToIndices()
            assert len(openLoops) == 2
            openLoop = openLoops[0]

            realNodes = [n for n in openLoop.nodes if isinstance(n, _mfn.RealNodeBase)]
            assert len(realNodes) == 1
            realNode = realNodes[0]

            outputVariables = realNode.serialize(nodesToIndices).outputVariables
            for outputVariable in outputVariables:
                if not outputVariable:
                    continue

                unitText += outputVariable.name + "\n"

            unitText += f"T{self.inputs[0].connectionList[0].displayName}\n"
            unitText += f"T{self.inputs[1].connectionList[0].displayName}\n"
            unitText += f"T{self.outputs[0].connectionList[0].displayName}\n"

            unitText += "***Initial values\n"
            unitText += 3 * "0 " + 3 * (str(ambientT) + " ") + "\n"

            unitText += "EQUATIONS 1\n"
            unitText += "T" + self.displayName + "= [" + str(unitNumber) + "," + str(equationConstant) + "]\n"

            unitNumber += 1
            f += unitText + "\n"

            return f, unitNumber
        else:
            return "", startingUnit
