from __future__ import annotations

import typing as _tp

import PyQt5.QtWidgets as _qtw

import trnsysGUI.connection.connectionBase as _cb
import trnsysGUI.connection.createMassFlowSolverNetworkPipes as _cmnp
import trnsysGUI.connection.deleteDoublePipeConnectionCommand as _ddpcc
import trnsysGUI.connection.doublePipeConnectionModel as _model
import trnsysGUI.connection.doublePipeDefaultValues as _defaults
import trnsysGUI.connection.hydraulicExport.common as _hecom
import trnsysGUI.connection.hydraulicExport.doublePipe as _he
import trnsysGUI.connection.hydraulicExport.doublePipe.createExportHydraulicDoublePipeConnection as _cehc
import trnsysGUI.connection.hydraulicExport.doublePipe.doublePipeConnection as _hedpc
import trnsysGUI.doublePipePortItem as _dppi
import trnsysGUI.internalPiping as _ip
import trnsysGUI.massFlowSolver.networkModel as _mfn
import trnsysGUI.names.undo as _nu
import trnsysGUI.segments.doublePipeSegmentItem as _dpsi
from . import _massFlowLabels as _mfl

if _tp.TYPE_CHECKING:
    import trnsysGUI.diagram.Editor as _ed


class DoublePipeConnection(_cb.ConnectionBase):  # pylint: disable=too-many-instance-attributes
    def __init__(
        self,
        displayName: str,
        fromPort: _dppi.DoublePipePortItem,
        toPort: _dppi.DoublePipePortItem,
        parent: _ed.Editor,  # type: ignore[name-defined]
    ) -> None:
        super().__init__(
            displayName,
            fromPort,
            toPort,
            _defaults.DEFAULT_SHALL_BE_SIMULATED,
            _defaults.DEFAULT_DOUBLE_PIPE_LENGTH_IN_M,
            parent,
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
        undoNamingHelper = _nu.UndoNamingHelper.create(self._editor.namesManager)

        undoCommand = _ddpcc.DeleteDoublePipeConnectionCommand(self, undoNamingHelper, parentCommand)
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

        self.setLabelPos(model.labelPos)
        self.setMassLabelPos(model.massFlowLabelPos)
        self.lengthInM = model.lengthInM
        self.shallBeSimulated = model.shallBeSimulated

        if len(model.segmentsCorners) > 0:
            self.loadSegments(model.segmentsCorners)

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

    def exportPipeAndTeeTypesForTemp(self, startingUnit: int) -> _tp.Tuple[str, int]:
        unitNumber = startingUnit

        exportModel = self._getHydraulicExportConnectionModel()
        return _he.export(exportModel, unitNumber)

    def _getHydraulicExportConnectionModel(self) -> _hedpc.ExportDoublePipeConnection:
        hydraulicConnection = _cehc.HydraulicDoublePipeConnection(
            self.displayName,
            _hecom.getAdjacentBlockItem(self.fromPort),
            _hecom.getAdjacentBlockItem(self.toPort),
            self.coldModelPipe,
            self.hotModelPipe,
        )

        exportHydraulicConnection = _cehc.createModel(hydraulicConnection)

        assert isinstance(self.lengthInM, float)

        exportConnection = _hedpc.ExportDoublePipeConnection(
            exportHydraulicConnection, self.lengthInM, self.shallBeSimulated
        )

        return exportConnection

    def _updateModels(self, newDisplayName: str):
        self.coldModelPipe, self.hotModelPipe = _cmnp.createMassFlowSolverNetworkPipes()

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
