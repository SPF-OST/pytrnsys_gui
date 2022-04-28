from __future__ import annotations

import typing as _tp

import trnsysGUI.connectors.doublePipeConnectorBase as _dpcb
import trnsysGUI.doublePipePortItem as _dppi
import trnsysGUI.images as _img
import trnsysGUI.massFlowSolver as _mfs
import trnsysGUI.massFlowSolver.networkModel as _mfn

from trnsysGUI import connectorsAndPipesExportHelpers as _helpers

if _tp.TYPE_CHECKING:
    import trnsysGUI.connection.doublePipeConnection as _dpc


class DoubleDoublePipeConnector(_dpcb.DoublePipeConnectorBase):
    def __init__(self, trnsysType, parent, **kwargs):
        super().__init__(trnsysType, parent, **kwargs)

        self.inputs.append(_dppi.DoublePipePortItem("i", 0, self))
        self.outputs.append(_dppi.DoublePipePortItem("o", 2, self))

        self.changeSize()

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

    def getInternalPiping(self) -> _mfs.InternalPiping:
        coldModelPortItemsToGraphicalPortItem = {
            self._coldPipe.fromPort: self.outputs[0],
            self._coldPipe.toPort: self.inputs[0],
        }

        hotModelPortItemsToGraphicalPortItem = {
            self._hotPipe.fromPort: self.inputs[0],
            self._hotPipe.toPort: self.outputs[0],
        }

        modelPortItemsToGraphicalPortItem = coldModelPortItemsToGraphicalPortItem | hotModelPortItemsToGraphicalPortItem

        internalPiping = _mfs.InternalPiping([self._coldPipe, self._hotPipe], modelPortItemsToGraphicalPortItem)

        return internalPiping

    def exportPipeAndTeeTypesForTemp(self, startingUnit: int) -> _tp.Tuple[str, int]:
        fromConnection = self.inputs[0].getConnection()
        toConnection = self.outputs[0].getConnection()

        hotEquation = self._getEquation("Hot", self._hotPipe, fromConnection, toConnection)
        coldEquation = self._getEquation("Cold", self._coldPipe, toConnection, fromConnection)

        equations = f"""\
EQUATIONS 2
{coldEquation}
{hotEquation}
"""
        return equations, startingUnit

    def _getEquation(
        self,
        temperatureSuffix: str,
        pipe: _mfn.Pipe,
        posFlowInputConnection: _dpc.DoublePipeConnection,
        negFlowInputConnection: _dpc.DoublePipeConnection,
    ) -> str:
        hotOutputTemp = f"T{self.displayName}{temperatureSuffix}"
        hotMfr = _helpers.getMfrName(pipe)
        posFlowHotInputTemp = f"T{posFlowInputConnection.displayName}{temperatureSuffix}"
        negFlowHotInputTemp = f"T{negFlowInputConnection.displayName}{temperatureSuffix}"
        hotEquation = _helpers.getEquation(
            hotOutputTemp, hotMfr, posFlowHotInputTemp, negFlowHotInputTemp
        )
        return hotEquation
