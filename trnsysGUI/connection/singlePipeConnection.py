from __future__ import annotations

import typing as _tp

import PyQt5.QtWidgets as _qtw

import trnsysGUI.connection.connectionBase as _cb
import trnsysGUI.connection.deleteSinglePipeConnectionCommand as _dspc
import trnsysGUI.connection.singlePipeConnectionModel as _model
import trnsysGUI.connection.values as _values
import trnsysGUI.hydraulicLoops.names as _names
import trnsysGUI.massFlowSolver as _mfs
import trnsysGUI.massFlowSolver.networkModel as _mfn
import trnsysGUI.singlePipePortItem as _sppi
import trnsysGUI.singlePipeSegmentItem as _spsi
from trnsysGUI import PortItemBase as _pib, BlockItem as _bi, TVentil as _tventil

if _tp.TYPE_CHECKING:
    import trnsysGUI.diagram.Editor as _ed


class SinglePipeConnection(_cb.ConnectionBase):  # pylint: disable=too-many-instance-attributes
    def __init__(
        self,
        fromPort: _sppi.SinglePipePortItem,
        toPort: _sppi.SinglePipePortItem,
        parent: _ed.Editor  # type: ignore[name-defined]
    ):
        super().__init__(fromPort, toPort, parent)

        self._editor = parent

        self.diameterInCm: _values.Value = _values.DEFAULT_DIAMETER_IN_CM
        self.uValueInWPerM2K: _values.Value = _values.DEFAULT_U_VALUE_IN_W_PER_M2_K
        self.lengthInM: _values.Value = _values.DEFAULT_LENGTH_IN_M

    @property
    def fromPort(self) -> _sppi.SinglePipePortItem:
        assert isinstance(self._fromPort, _sppi.SinglePipePortItem)
        return self._fromPort

    @property
    def toPort(self) -> _sppi.SinglePipePortItem:
        assert isinstance(self._toPort, _sppi.SinglePipePortItem)
        return self._toPort

    def _createSegmentItem(self, startNode, endNode):
        return _spsi.SinglePipeSegmentItem(startNode, endNode, self)

    def getRadius(self):
        rad = 2
        return rad

    def editHydraulicLoop(self) -> None:
        self._editor.editHydraulicLoop(self)

    def createDeleteUndoCommand(self, parentCommand: _tp.Optional[_qtw.QUndoCommand] = None) -> _qtw.QUndoCommand:
        undoCommand = _dspc.DeleteSinglePipeConnectionCommand(
            self, self._editor.hydraulicLoops, self._editor.fluids.fluids, self._editor.fluids.WATER, parentCommand
        )

        return undoCommand

    def encode(self):
        if len(self.segments) > 0:
            labelPos = self.segments[0].label.pos().x(), self.segments[0].label.pos().y()
            labelMassPos = self.segments[0].labelMass.pos().x(), self.segments[0].labelMass.pos().y()
        else:
            self.logger.debug("This connection has no segment")
            defaultPos = self.fromPort.pos().x(), self.fromPort.pos().y()  # pylint: disable = duplicate-code # 2
            labelPos = defaultPos
            labelMassPos = defaultPos

        corners = []
        for s in self.getCorners():  # pylint: disable=invalid-name
            cornerTupel = (s.pos().x(), s.pos().y())
            corners.append(cornerTupel)

        connectionModel = _model.ConnectionModel(
            self.connId,
            self.displayName,
            self.id,
            corners,
            labelPos,
            labelMassPos,
            self.fromPort.id,
            self.toPort.id,
            self.trnsysId,
            self.diameterInCm,
            self.uValueInWPerM2K,
            self.lengthInM,
        )

        dictName = "Connection-"
        return dictName, connectionModel.to_dict()

    def decode(self, i):
        model = _model.ConnectionModel.from_dict(i)

        self.id = model.id
        self.connId = model.connectionId
        self.trnsysId = model.trnsysId
        self.setDisplayName(model.name)

        if len(model.segmentsCorners) > 0:
            self.loadSegments(model.segmentsCorners)

        self.setLabelPos(model.labelPos)
        self.setMassLabelPos(model.massFlowLabelPos)

        self.diameterInCm = model.diameterInCm
        self.uValueInWPerM2K = model.uValueInWPerM2K
        self.lengthInM = model.lengthInM

    def getInternalPiping(self) -> _mfs.InternalPiping:
        fromPort = _mfn.PortItem("Input", _mfn.PortItemType.INPUT)
        toPort = _mfn.PortItem("Output", _mfn.PortItemType.OUTPUT)

        pipe = _mfn.Pipe(self.displayName, self.trnsysId, fromPort, toPort)
        return _mfs.InternalPiping([pipe], {fromPort: self.fromPort, toPort: self.toPort})

    def exportPipeAndTeeTypesForTemp(self, startingUnit):  # pylint: disable=too-many-locals, too-many-statements
        lines = ""
        unitNumber = startingUnit
        typeNr2 = 931  # Temperature calculation from a pipe

        unitText = ""
        ambientT = 20

        loop = self._editor.hydraulicLoops.getLoopForExistingConnection(self)

        densityVar = _names.getDensityName(loop.name.value)
        specHeatVar = _names.getHeatCapacityName(loop.name.value)

        equationConstant1 = 1
        equationConstant2 = 3

        parameterNumber = 6
        inputNumbers = 4

        # Fixed strings
        tempRoomVar = "TRoomStore"
        initialValueS = "20 0.0 20 20"
        powerPrefix = "P"

        # Momentarily hardcoded
        equationNr = 3

        unitText += "UNIT " + str(unitNumber) + " TYPE " + str(typeNr2) + "\n"
        unitText += "!" + self.displayName + "\n"
        unitText += "PARAMETERS " + str(parameterNumber) + "\n"

        lengthInM = _getConvertedValueOrName(self.lengthInM)
        diameterInM = _getConvertedValueOrName(self.diameterInCm, 1 / 100)
        uValueInkJPerHourM2K = _getConvertedValueOrName(self.uValueInWPerM2K, 60 * 60 / 1000)

        unitText += f"{diameterInM} ! diameter [m]\n"
        unitText += f"{lengthInM} ! length [m]\n"

        uValueInSIUnitsComment = (
            f" (= {self.uValueInWPerM2K} W/(m^2*K))" if isinstance(self.uValueInWPerM2K, float) else ""
        )
        unitText += f"{uValueInkJPerHourM2K} ! U-value [kJ/(h*m^2*K)]{uValueInSIUnitsComment}\n"

        unitText += densityVar + "\n"
        unitText += specHeatVar + "\n"
        unitText += str(ambientT) + "\n"

        unitText += "INPUTS " + str(inputNumbers) + "\n"

        openLoops, _ = self._getOpenLoopsAndNodeToIndices()
        assert len(openLoops) == 1
        openLoop = openLoops[0]

        assert len(openLoop.realNodes) == 1
        realNode = openLoop.realNodes[0]

        outputVariables = realNode.getOutputVariables()

        portItemsWithParent = self._getFromAndToPortsAndParentBlockItems()

        if len(portItemsWithParent) == 2:
            portItem = portItemsWithParent[0][0]
            parent = portItemsWithParent[0][1]
            if hasattr(parent, "getSubBlockOffset"):
                unitText += "T" + parent.displayName + "X" + str(parent.getSubBlockOffset(self) + 1) + "\n"
            else:
                unitText += parent.getTemperatureVariableName(portItem) + "\n"

            unitText += f"{outputVariables[0].name}\n"
            unitText += tempRoomVar + "\n"

            portItem = portItemsWithParent[1][0]
            parent = portItemsWithParent[1][1]
            if hasattr(parent, "getSubBlockOffset"):
                unitText += "T" + parent.displayName + "X" + str(parent.getSubBlockOffset(self) + 1) + "\n"
            else:
                unitText += parent.getTemperatureVariableName(portItem) + "\n"

        else:
            lines += (
                "Error: NO VALUE\n" * 3
                + "at connection with parents "
                + str(self.fromPort.parent)
                + str(self.toPort.parent)
                + "\n"
            )

        unitText += "***Initial values\n"
        unitText += initialValueS + "\n\n"

        unitText += "EQUATIONS " + str(equationNr) + "\n"
        unitText += "T" + self.displayName + "= [" + str(unitNumber) + "," + str(equationConstant1) + "]\n"
        unitText += (
            powerPrefix
            + self.displayName
            + "_kW"
            + "= ["
            + str(unitNumber)
            + ","
            + str(equationConstant2)
            + "]/3600 !kW\n"
        )
        unitText += "Mfr" + self.displayName + "= " + "Mfr" + self.displayName + "_A\n\n"

        unitNumber += 1

        return unitText, unitNumber

    def _getFromAndToPortsAndParentBlockItems(
        self,
    ) -> _tp.Tuple[_tp.Tuple[_pib.PortItemBase, _bi.BlockItem], _tp.Tuple[_pib.PortItemBase, _bi.BlockItem]]:
        isToPortValveOutput = (
            isinstance(self.toPort.parent, _tventil.TVentil) and self.fromPort in self.toPort.parent.outputs
        )
        if isToPortValveOutput:
            return (self.toPort, self.toPort.parent), (self.fromPort, self.fromPort.parent)

        return (self.fromPort, self.fromPort.parent), (self.toPort, self.toPort.parent)


def _getConvertedValueOrName(valueOrName: _values.Value, conversionFactor=1.0) -> _tp.Union[float, str]:
    if isinstance(valueOrName, _values.Variable):
        return valueOrName.name

    value = valueOrName

    return value * conversionFactor
