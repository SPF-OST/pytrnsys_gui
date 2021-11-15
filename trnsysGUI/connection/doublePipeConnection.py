# pylint: skip-file
# type: ignore

from __future__ import annotations

import math as _math
import typing as _tp

import massFlowSolver as _mfs
import massFlowSolver.networkModel as _mfn
from massFlowSolver import InternalPiping
from massFlowSolver.modelPortItems import ColdPortItem, HotPortItem
from trnsysGUI.Connection import Connection
from trnsysGUI.PortItemBase import PortItemBase
from trnsysGUI.connection.segmentItemFactory import SegmentItemFactoryBase

if _tp.TYPE_CHECKING:
    pass


def calcDist(p1, p2):
    vec = p1 - p2
    norm = _math.sqrt(vec.x() ** 2 + vec.y() ** 2)
    return norm


class DoublePipeConnection(Connection):
    def __init__(self, fromPort: PortItemBase, toPort: PortItemBase, segmentItemFactory: SegmentItemFactoryBase, parent):
        super().__init__(fromPort, toPort, segmentItemFactory, parent)

        self.childIds = []
        self.childIds.append(self.trnsysId)
        self.childIds.append(self.parent.idGen.getTrnsysID())

    # Saving / Loading
    def encode(self):
        self.logger.debug("Encoding a connection")

        dct = {}
        dct[".__ConnectionDict__"] = True
        dct["fromPortId"] = self.fromPort.id
        dct["toPortId"] = self.toPort.id
        dct["name"] = self.displayName
        dct["id"] = self.id
        dct["connectionId"] = self.connId
        dct["trnsysId"] = self.trnsysId
        dct["childIds"] = self.childIds
        dct["groupName"] = self.groupName

        if len(self.segments) > 0:
            dct["labelPos"] = self.segments[0].label.pos().x(), self.segments[0].label.pos().y()
            dct["massFlowLabelPos"] = self.segments[0].labelMass.pos().x(), self.segments[0].labelMass.pos().y()
        else:
            defaultPos = self.fromPort.pos().x(), self.fromPort.pos().y()
            dct["labelPos"] = defaultPos
            dct["massFlowLabelPos"] = defaultPos

        corners = []
        for s in self.getCorners():
            cornerTupel = (s.pos().x(), s.pos().y())
            corners.append(cornerTupel)

        dct["segmentsCorners"] = corners

        dictName = "Connection-"

        return dictName, dct

    def decode(self, i):
        self.logger.debug("Loading a connection in Decoder")

        self.id = i["id"]
        self.connId = i["connectionId"]
        self.trnsysId = i["trnsysId"]
        self.childIds = i["childIds"]
        self.setName(i["name"])
        self.groupName = "defaultGroup"
        self.setConnToGroup(i["groupName"])

        if len(i["segmentsCorners"]) > 0:
            self.loadSegments(i["segmentsCorners"])

        self.setLabelPos(i["labelPos"])
        self.setMassLabelPos(i["massFlowLabelPos"])

    def getInternalPiping(self) -> InternalPiping:
        coldFromPort = ColdPortItem()
        coldToPort = ColdPortItem()
        coldPipe = _mfn.Pipe(self.displayName + "Cold", self.childIds[0], coldFromPort, coldToPort)
        ColdModelPortItemsToGraphicalPortItem = {coldFromPort: self.fromPort, coldToPort: self.toPort}

        hotFromPort = HotPortItem()
        hotToPort = HotPortItem()
        hotPipe = _mfn.Pipe(self.displayName + "Hot", self.childIds[1], hotFromPort, hotToPort)
        HotModelPortItemsToGraphicalPortItem = {hotFromPort: self.fromPort, hotToPort: self.toPort}

        ModelPortItemsToGraphicalPortItem = ColdModelPortItemsToGraphicalPortItem | HotModelPortItemsToGraphicalPortItem
        return InternalPiping([coldPipe, hotPipe], ModelPortItemsToGraphicalPortItem)

    def _getConnectedRealNode(self, portItem, internalPiping) -> _tp.Optional[_mfn.RealNodeBase]:
        assert portItem in internalPiping.modelPortItemsToGraphicalPortItem, "`portItem' doesn't belong to `internalPiping'"

        graphicalPortItem = internalPiping.modelPortItemsToGraphicalPortItem[portItem]

        assert graphicalPortItem in [self.fromPort, self.toPort], \
            "This connection is not connected to `graphicalPortItem'"

        blockItem: _mfs.MassFlowNetworkContributorMixin = graphicalPortItem.parent
        blockItemInternalPiping = blockItem.getInternalPiping()

        for startingNode in blockItemInternalPiping.openLoopsStartingNodes:
            realNodesAndPortItems = _mfn.getConnectedRealNodesAndPortItems(startingNode)
            for realNode in realNodesAndPortItems.realNodes:
                for candidatePortItem in [n for n in realNode.getNeighbours() if type(n) is type(portItem)]:
                    candidateGraphicalPortItem = blockItemInternalPiping.modelPortItemsToGraphicalPortItem[
                        candidatePortItem]
                    if candidateGraphicalPortItem == graphicalPortItem:
                        return realNode
        return None

    def exportPipeAndTeeTypesForTemp(self, startingUnit):
        unitNumber = startingUnit
        typeNr2 = 9511  # Temperature calculation from a pipe

        unitText = ""
        ambientT = 20

        densityVar = "RhoWat"
        specHeatVar = "CPWat"

        parameterNumber = 6
        inputNumbers = 6

        # Fixed strings
        diameterPrefix = "di"
        lengthPrefix = "L"
        lossPrefix = "U"
        tempRoomVar = "TRoomStore"
        initialValueS = "15.0 0.0 15.0 15.0 0.0 15.0"
        powerPrefix = "P"

        # Momentarily hardcoded
        equationNr = 6

        unitText += "UNIT " + str(unitNumber) + " TYPE " + str(typeNr2) + "\n"
        unitText += "!" + self.displayName + "\n"
        unitText += "PARAMETERS " + str(parameterNumber) + "\n"

        unitText += diameterPrefix + self.displayName + "\n"
        unitText += lengthPrefix + self.displayName + "\n"
        unitText += lossPrefix + self.displayName + "\n"
        unitText += densityVar + "\n"
        unitText += specHeatVar + "\n"
        unitText += str(ambientT) + "\n"

        unitText += "INPUTS " + str(inputNumbers) + "\n"

        openLoops, nodesToIndices = self._getOpenLoopsAndNodeToIndices()
        assert len(openLoops) == 2
        temps = ["Cold", "Hot"]
        for openLoop, temp in zip(openLoops, temps):
            realNodes = [n for n in openLoop.nodes if isinstance(n, _mfn.RealNodeBase)]
            assert len(realNodes) == 1
            realNode = realNodes[0]

            outputVariables = realNode.serialize(nodesToIndices).outputVariables

            portItemsWithParent = self._getPortItemsWithParent()

            assert len(portItemsWithParent) == 2

            portItem = portItemsWithParent[0][0]
            parent = portItemsWithParent[0][1]

            firstColumn = f"T{self.displayName}{temp}"
            unitText += self.addComment(firstColumn, f"! Inlet fluid temperature - Pipe {temp}, deg C")

            firstColumn = f"{outputVariables[0].name}"
            unitText += self.addComment(firstColumn, f"! Inlet fluid flow rate - Pipe {temp}, kJ/h")

            portItem = portItemsWithParent[1][0]
            parent = portItemsWithParent[1][1]
            firstColumn = f"T{self.displayName}{temp}"
            unitText += self.addComment(firstColumn, "! Other side of pipe, deg C")

        unitText += "***Initial values\n"
        unitText += initialValueS + "\n\n"

        unitText += "EQUATIONS " + str(equationNr) + "\n"

        equationConstant1 = 1
        equationConstant2 = 3
        equationConstants = [equationConstant1, equationConstant2]

        for openLoop, temp, equationConstant in zip(openLoops, temps, equationConstants):
            firstColumn = "T" + self.displayName + temp + " = [" + str(unitNumber) + "," + str(equationConstant) + "]"
            unitText += self.addComment(firstColumn, f"! {equationConstant}: Outlet fluid temperature pipe {temp}, deg C")

            realNodes = [n for n in openLoop.nodes if isinstance(n, _mfn.RealNodeBase)]
            assert len(realNodes) == 1
            realNode = realNodes[0]

            outputVariables = realNode.serialize(nodesToIndices).outputVariables

            firstColumn = f"Mfr{self.displayName}{temp} = {outputVariables[0].name}"
            unitText += self.addComment(firstColumn, f"! Outlet mass flow rate pipe {temp}, kg/h")

        equationConstant1 = 7
        equationConstant2 = 8
        equationConstants = [equationConstant1, equationConstant2]

        for openLoop, temp, equationConstant in zip(openLoops, temps, equationConstants):
            firstColumn = f"P{self.displayName}{temp}_kW = [{unitNumber},{equationConstant}]/3600"
            unitText += self.addComment(firstColumn, f"! {equationConstant}: Delivered energy pipe {temp}, kJ/h")

        unitNumber += 1
        unitText += "\n\n"

        return unitText, unitNumber
