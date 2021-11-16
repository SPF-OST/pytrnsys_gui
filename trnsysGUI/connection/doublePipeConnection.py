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
from trnsysGUI.doublePipeSegmentItem import DoublePipeSegmentItem

if _tp.TYPE_CHECKING:
    pass


class DoublePipeConnection(Connection):
    def __init__(self, fromPort: PortItemBase, toPort: PortItemBase, parent):
        super().__init__(fromPort, toPort, parent)

        self.childIds = []
        self.childIds.append(self.trnsysId)
        self.childIds.append(self.parent.idGen.getTrnsysID())

    def _createSegmentItem(self, startNode, endNode):
        return DoublePipeSegmentItem(startNode, endNode, self)

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
        commentStars = 6 * "*"

        parameterNumber = 35
        inputNumbers = 6

        # default values
        lPipe = 24.384
        diPipe = 0.02618
        doPipe = 0.03198
        cpPipe = 1.37067
        depthPipe = 3.0
        dirSecondPipe = 1
        dCasing = 0.17526
        condInsulation = 0.14537
        xPipeToPipe = 0.06911
        condCap = 8.722
        dGap = 0.0000

        rhoFluidPipe = 1000.0
        condFluidPipe = 2.2068
        cpFluidPipe = 4.19
        viscFluidPipe = 3.078

        TiniPipeHot = 10.0
        TiniPipeCold = 10.0

        condSoil = 8.722
        rhoSoil = 2500.0
        cpSoil = 0.84

        TSurfArg = 7.96
        AmplSurfAvg = 13.32
        DayMinSfT = 36

        nCvFluid = 100
        nCvRad = 8
        nCvAXSoil = 10
        nCvCircSoil = 4
        dRadn1 = 0.0254

        # Fixed strings
        initialValueS = "15.0 0.0 15.0 15.0 0.0 15.0"

        # Momentarily hardcoded
        equationNr = 6

        unitText += "UNIT " + str(unitNumber) + " TYPE " + str(typeNr2) + "\n"
        unitText += "!" + self.displayName + "\n"

        unitText += "PARAMETERS " + str(parameterNumber) + "\n"
        unitText += commentStars + " pipe and soil properties " + commentStars + "\n"
        unitText += self.addComment(lPipe, "! Length of buried pipe")
        unitText += self.addComment(diPipe, "! Inner diameter of pipes")
        unitText += self.addComment(doPipe, "! Outer diameter of pipes")
        unitText += self.addComment(cpPipe, "! Thermal conductivity of pipe material")
        unitText += self.addComment(depthPipe, "! Buried pipe depth")
        unitText += self.addComment(dirSecondPipe, "! Direction of second pipe flow")
        unitText += self.addComment(dCasing, "! Diameter of casing material	")
        unitText += self.addComment(condInsulation, "! Thermal conductivity of fill insulation")
        unitText += self.addComment(xPipeToPipe, "! Center-to-center pipe spacing")
        unitText += self.addComment(condCap, "! Thermal conductivity of gap material")
        unitText += self.addComment(dGap, "! Gap thickness")

        unitText += commentStars + " fluid properties " + commentStars + "\n"
        unitText += self.addComment(rhoFluidPipe, "! Density of fluid")
        unitText += self.addComment(condFluidPipe, "! Thermal conductivity of fluid")
        unitText += self.addComment(cpFluidPipe, "! Specific heat of fluid")
        unitText += self.addComment(viscFluidPipe, "! Viscosity of fluid")

        unitText += commentStars + " initial conditions " + commentStars + "\n"
        unitText += self.addComment(TiniPipeHot, "! Initial fluid temperature - Pipe hot")
        unitText += self.addComment(TiniPipeCold, "! Initial fluid temperature - Pipe cold")

        unitText += commentStars + " thermal properties soil " + commentStars + "\n"
        unitText += self.addComment(condSoil, "! Thermal conductivity of soil")
        unitText += self.addComment(rhoSoil, "! Density of soil")
        unitText += self.addComment(cpSoil, "! Specific heat of soil")

        unitText += commentStars + " general temperature dependency (dependent from weather data) " + commentStars + "\n"
        unitText += self.addComment(TSurfArg, "! Average surface temperature")
        unitText += self.addComment(AmplSurfAvg, "! Amplitude of surface temperature")
        unitText += self.addComment(DayMinSfT, "! Day of minimum surface temperature")

        unitText += commentStars + " definition of nodes " + commentStars + "\n"
        unitText += self.addComment(nCvFluid, "! Number of fluid nodes")
        unitText += self.addComment(nCvRad, "! Number of radial soil nodes")
        unitText += self.addComment(nCvAXSoil, "! Number of axial soil nodes")
        unitText += self.addComment(nCvCircSoil, "! Number of circumferential soil nodes")
        unitText += self.addComment(dRadn1, "! Radial distance of node -1")
        unitText += self.addComment(dRadn1, "! Radial distance of node -2")
        unitText += self.addComment(dRadn1, "! Radial distance of node -3")
        unitText += self.addComment(dRadn1, "! Radial distance of node -4")
        unitText += self.addComment(dRadn1, "! Radial distance of node -5")
        unitText += self.addComment(dRadn1, "! Radial distance of node -6")
        unitText += self.addComment(dRadn1, "! Radial distance of node -7")
        unitText += self.addComment(dRadn1, "! Radial distance of node -8")

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

            parent = portItemsWithParent[0][1]

            firstColumn = f"T{parent.displayName}{temp}"
            unitText += self.addComment(firstColumn, f"! Inlet fluid temperature - Pipe {temp}, deg C")

            firstColumn = f"{outputVariables[0].name}"
            unitText += self.addComment(firstColumn, f"! Inlet fluid flow rate - Pipe {temp}, kJ/h")

            parent = portItemsWithParent[1][1]
            firstColumn = f"T{parent.displayName}{temp}"
            unitText += self.addComment(firstColumn, "! Other side of pipe, deg C")

        unitText += "***Initial values\n"
        unitText += initialValueS + "\n\n"

        unitText += "EQUATIONS " + str(equationNr) + "\n"

        equationConstant1 = 1
        equationConstant3 = 3
        firstEquationConstants = [equationConstant1, equationConstant3]

        equationConstant7 = 7
        equationConstant8 = 8
        secondEquationConstants = [equationConstant7, equationConstant8]

        for openLoop, temp, firstEquationConstant, secondEquationConstant \
                in zip(openLoops, temps, firstEquationConstants, secondEquationConstants):
            firstColumn = "T" + self.displayName + temp + " = [" + str(unitNumber) + "," + str(
                firstEquationConstant) + "]"
            unitText += self.addComment(firstColumn,
                                        f"! {firstEquationConstant}: Outlet fluid temperature pipe {temp}, deg C")

            realNodes = [n for n in openLoop.nodes if isinstance(n, _mfn.RealNodeBase)]
            assert len(realNodes) == 1
            realNode = realNodes[0]

            outputVariables = realNode.serialize(nodesToIndices).outputVariables

            firstColumn = f"Mfr{self.displayName}{temp} = {outputVariables[0].name}"
            unitText += self.addComment(firstColumn, f"! Outlet mass flow rate pipe {temp}, kg/h")

            firstColumn = f"P{self.displayName}{temp}_kW = [{unitNumber},{secondEquationConstant}]/3600"
            unitText += self.addComment(firstColumn, f"! {secondEquationConstant}: Delivered energy pipe {temp}, kJ/h")

        unitNumber += 1
        unitText += "\n"

        return unitText, unitNumber
