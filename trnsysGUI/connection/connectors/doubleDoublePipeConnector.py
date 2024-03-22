from __future__ import annotations

import typing as _tp

import trnsysGUI.connection.connectors.doublePipeConnectorBase as _dpcb
import trnsysGUI.connection.createMassFlowSolverNetworkPipes as _cmnp
import trnsysGUI.connection.hydraulicExport.common as _hecom
import trnsysGUI.connection.hydraulicExport.doublePipe.createExportHydraulicDoublePipeConnection as _cehc
import trnsysGUI.connection.hydraulicExport.doublePipe.dummy as _he
import trnsysGUI.doublePipePortItem as _dppi
import trnsysGUI.images as _img
import trnsysGUI.internalPiping as _ip


class DoubleDoublePipeConnector(_dpcb.DoublePipeConnectorBase):
    def __init__(self, trnsysType: str, editor, displayName: str) -> None:
        super().__init__(trnsysType, editor, displayName)

        self.fromPort = _dppi.DoublePipePortItem("i", 0, self)
        self.toPort = _dppi.DoublePipePortItem("o", 2, self)

        self.inputs.append(self.fromPort)
        self.outputs.append(self.toPort)

        self._updateModels(self.displayName)

        self.changeSize()

    def _updateModels(self, newDisplayName: str) -> None:
        self._coldPipe, self._hotPipe = _cmnp.createMassFlowSolverNetworkPipes()

    def _getImageAccessor(self) -> _tp.Optional[_img.ImageAccessor]:
        return _img.DOUBLE_DOUBLE_PIPE_CONNECTOR_SVG

    def changeSize(self):
        super().changeSize()

        self.origInputsPos = [[0, 10]]
        self.origOutputsPos = [[40, 10]]

        self.inputs[0].setPos(self.origInputsPos[0][0], self.origInputsPos[0][1])
        self.outputs[0].setPos(self.origOutputsPos[0][0], self.origOutputsPos[0][1])

        # pylint: disable=duplicate-code  # 3
        self.updateFlipStateH(self.flippedH)
        self.updateFlipStateV(self.flippedV)

        self.inputs[0].side = (self.rotationN + 2 * self.flippedH) % 4
        self.outputs[0].side = (self.rotationN + 2 - 2 * self.flippedH) % 4

    def getInternalPiping(self) -> _ip.InternalPiping:
        coldModelPortItemsToGraphicalPortItem = {
            self._coldPipe.fromPort: self.outputs[0],
            self._coldPipe.toPort: self.inputs[0],
        }

        hotModelPortItemsToGraphicalPortItem = {
            self._hotPipe.fromPort: self.inputs[0],
            self._hotPipe.toPort: self.outputs[0],
        }

        modelPortItemsToGraphicalPortItem = coldModelPortItemsToGraphicalPortItem | hotModelPortItemsToGraphicalPortItem

        internalPiping = _ip.InternalPiping([self._coldPipe, self._hotPipe], modelPortItemsToGraphicalPortItem)

        return internalPiping

    def exportPipeAndTeeTypesForTemp(self, startingUnit: int) -> _tp.Tuple[str, int]:
        hydraulicConnection = _cehc.HydraulicDoublePipeConnection(
            self.displayName,
            _hecom.getAdjacentConnection(self.fromPort),
            _hecom.getAdjacentConnection(self.toPort),
            self._coldPipe,
            self._hotPipe,
        )

        hydraulicExportConnection = _cehc.createModel(hydraulicConnection)

        unitNumber = startingUnit
        return _he.exportDummyConnection(
            hydraulicExportConnection, unitNumber, shallDefineCanonicalMassFlowVariables=False
        )
