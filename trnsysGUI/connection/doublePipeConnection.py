from __future__ import annotations

import typing as _tp

import PyQt5.QtWidgets as _qtw

import trnsysGUI.connection.connectionBase as _cb
import trnsysGUI.connection.doublePipeConnectionModel as _model
import trnsysGUI.connection.doublePipeDefaultValues as _defaults
import trnsysGUI.connection.hydraulicExport.doublePipe as _he
import trnsysGUI.connection.hydraulicExport.doublePipe.doublePipeConnection as _hedpc
import trnsysGUI.connectorsAndPipesExportHelpers as _helpers
import trnsysGUI.doublePipePortItem as _dppi
import trnsysGUI.doublePipeSegmentItem as _dpsi
import trnsysGUI.internalPiping as _ip
import trnsysGUI.massFlowSolver.networkModel as _mfn
from . import _massFlowLabels as _mfl


class DoublePipeConnection(_cb.ConnectionBase):  # pylint: disable=too-many-instance-attributes
    def __init__(self, fromPort: _dppi.DoublePipePortItem, toPort: _dppi.DoublePipePortItem, parent):
        super().__init__(
            fromPort, toPort, _defaults.DEFAULT_SHALL_BE_SIMULATED, _defaults.DEFAULT_DOUBLE_PIPE_LENGTH_IN_M, parent
        )

        self.childIds = []
        self.childIds.append(self.trnsysId)
        self.childIds.append(self.parent.idGen.getTrnsysID())

        self._updateModels(self.displayName)

    @property
    def fromPort(self) -> _dppi.DoublePipePortItem:
        assert isinstance(self._fromPort, _dppi.DoublePipePortItem)
        return self._fromPort

    @property
    def toPort(self) -> _dppi.DoublePipePortItem:
        assert isinstance(self._toPort, _dppi.DoublePipePortItem)
        return self._toPort

    def getModelPipe(self, portItemType: _mfn.PortItemType) -> _mfn.Pipe:
        if portItemType == _mfn.PortItemType.COLD:
            return self.coldModelPipe

        if portItemType == _mfn.PortItemType.HOT:
            return self.hotModelPipe

        raise ValueError(f"Don't have a model pipe of type {portItemType}.")

    def _createSegmentItem(self, startNode, endNode):
        return _dpsi.DoublePipeSegmentItem(startNode, endNode, self)

    def getRadius(self):
        rad = 4
        return rad

    def createDeleteUndoCommand(self, parentCommand: _tp.Optional[_qtw.QUndoCommand] = None) -> _qtw.QUndoCommand:
        undoCommand = DeleteDoublePipeConnectionCommand(self, parentCommand)
        return undoCommand

    def encode(self):
        if len(self.segments) > 0:
            labelPos = self.segments[0].label.pos().x(), self.segments[0].label.pos().y()
            labelMassPos = self.segments[0].labelMass.pos().x(), self.segments[0].labelMass.pos().y()
        else:
            self.logger.debug("This connection has no segment")
            defaultPos = self.fromPort.pos().x(), self.fromPort.pos().y()  # pylint: disable = duplicate-code # 1
            labelPos = defaultPos
            labelMassPos = defaultPos

        corners = []
        for corner in self.getCorners():
            cornerTupel = (corner.pos().x(), corner.pos().y())
            corners.append(cornerTupel)

        doublePipeConnectionModel = _model.DoublePipeConnectionModel(
            self.connId,
            self.displayName,
            self.id,
            self.childIds,
            corners,
            labelPos,
            labelMassPos,
            self.fromPort.id,
            self.toPort.id,
            self.trnsysId,
            self.lengthInM,
            self.shallBeSimulated,
        )

        dictName = "Connection-"
        return dictName, doublePipeConnectionModel.to_dict()

    def decode(self, i):
        model = _model.DoublePipeConnectionModel.from_dict(i)

        self.id = model.id
        self.connId = model.connectionId
        self.trnsysId = model.trnsysId
        self.childIds = model.childIds
        self.setDisplayName(model.name)

        if len(model.segmentsCorners) > 0:
            self.loadSegments(model.segmentsCorners)

        self.setLabelPos(model.labelPos)
        self.setMassLabelPos(model.massFlowLabelPos)
        self.lengthInM = model.lengthInM
        self.shallBeSimulated = model.shallBeSimulated

    def getInternalPiping(self) -> _ip.InternalPiping:
        coldModelPortItemsToGraphicalPortItem = {
            self.coldModelPipe.fromPort: self.toPort,
            self.coldModelPipe.toPort: self.fromPort,
        }

        hotModelPortItemsToGraphicalPortItem = {
            self.hotModelPipe.fromPort: self.fromPort,
            self.hotModelPipe.toPort: self.toPort,
        }

        modelPortItemsToGraphicalPortItem = coldModelPortItemsToGraphicalPortItem | hotModelPortItemsToGraphicalPortItem
        return _ip.InternalPiping([self.coldModelPipe, self.hotModelPipe], modelPortItemsToGraphicalPortItem)

    def exportPipeAndTeeTypesForTemp(
        self, startingUnit: int
    ) -> _tp.Tuple[str, int]:  # pylint: disable=too-many-locals,too-many-statements
        unitNumber = startingUnit

        exportModel = self._getHydraulicExportConnectionModel()
        return _he.export(exportModel, unitNumber)

    def _getHydraulicExportConnectionModel(self) -> _hedpc.DoublePipeConnection:
        coldInputTemperature = _helpers.getTemperatureVariableName(
            self.toPort.parent, self.toPort, _mfn.PortItemType.COLD
        )
        coldMassFlowRate = _helpers.getInputMfrName(self, self.coldModelPipe)
        coldRevInputTemperature = _helpers.getTemperatureVariableName(
            self.fromPort.parent, self.fromPort, _mfn.PortItemType.COLD
        )

        hotInputTemperature = _helpers.getTemperatureVariableName(
            self.fromPort.parent, self.fromPort, _mfn.PortItemType.HOT
        )
        hotMassFlowRate = _helpers.getInputMfrName(self, self.hotModelPipe)
        hotRevInputTemperature = _helpers.getTemperatureVariableName(
            self.toPort.parent, self.toPort, _mfn.PortItemType.HOT
        )

        # This assert is only used to satisfy MyPy, because we know that for double pipes, these have names.
        assert self.coldModelPipe.name and self.hotModelPipe.name

        connectionModel = _hedpc.DoublePipeConnection(
            self.displayName,
            self.lengthInM,
            self.shallBeSimulated,
            coldPipe=_hedpc.SinglePipe(
                self.coldModelPipe.name,
                _hedpc.InputPort(coldInputTemperature, coldMassFlowRate),
                _hedpc.OutputPort(coldRevInputTemperature),
            ),
            hotPipe=_hedpc.SinglePipe(
                self.hotModelPipe.name,
                _hedpc.InputPort(hotInputTemperature, hotMassFlowRate),
                _hedpc.OutputPort(hotRevInputTemperature),
            ),
        )
        return connectionModel

    def _updateModels(self, newDisplayName: str):
        coldFromPort: _mfn.PortItem = _mfn.PortItem("In", _mfn.PortItemDirection.INPUT, _mfn.PortItemType.COLD)
        coldToPort: _mfn.PortItem = _mfn.PortItem("Out", _mfn.PortItemDirection.OUTPUT, _mfn.PortItemType.COLD)
        self.coldModelPipe = _mfn.Pipe(coldFromPort, coldToPort, name="Cold")

        hotFromPort: _mfn.PortItem = _mfn.PortItem("In", _mfn.PortItemDirection.INPUT, _mfn.PortItemType.HOT)
        hotToPort: _mfn.PortItem = _mfn.PortItem("Out", _mfn.PortItemDirection.OUTPUT, _mfn.PortItemType.HOT)
        self.hotModelPipe = _mfn.Pipe(hotFromPort, hotToPort, name="Hot")

    def setMassFlowAndTemperature(
        self, coldMassFlow: float, coldTemperature: float, hotMassFlow: float, hotTemperature: float
    ) -> None:
        formattedColdMassFlowAndTemperature = _mfl.getFormattedMassFlowAndTemperature(coldMassFlow, coldTemperature)
        formattedHotMassFlowAndTemperature = _mfl.getFormattedMassFlowAndTemperature(hotMassFlow, hotTemperature)
        labelText = f"""\
Cold: {formattedColdMassFlowAndTemperature}
Hot: {formattedHotMassFlowAndTemperature}
"""
        for segment in self.segments:
            segment.labelMass.setPlainText(labelText)


class DeleteDoublePipeConnectionCommand(_qtw.QUndoCommand):
    def __init__(
        self, doublePipeConnection: DoublePipeConnection, parentCommand: _tp.Optional[_qtw.QUndoCommand] = None
    ) -> None:
        super().__init__("Delete double pipe connection", parentCommand)
        self._connection = doublePipeConnection
        self._fromPort = self._connection.fromPort
        self._toPort = self._connection.toPort
        self._editor = self._connection.parent

    def undo(self):
        self._connection = DoublePipeConnection(self._fromPort, self._toPort, self._editor)

    def redo(self):
        self._connection.deleteConn()
        self._connection = None
