import typing as _tp

import trnsysGUI.images as _img
import trnsysGUI.massFlowSolver.networkModel as _mfn
import trnsysGUI.temperatures as _temps

from . import _tapBase as _tb


class TapMains(_tb.TapBase):
    def __init__(self, trnsysType, editor, **kwargs):
        super().__init__(trnsysType, editor, _mfn.PortItemDirection.OUTPUT, **kwargs)

    def _getImageAccessor(self) -> _tp.Optional[_img.ImageAccessor]:
        return _img.TAP_MAINS_SVG

    def _getCanonicalMassFlowRate(self) -> float:
        return self._massFlowRateInKgPerH

    def exportPipeAndTeeTypesForTemp(self, startingUnit: int) -> _tp.Tuple[str, int]:
        temperatureVariable = _temps.getTemperatureVariableName(
            self.shallRenameOutputTemperaturesInHydraulicFile(),
            componentDisplayName=self.displayName,
            nodeName=self._modelTerminal.name,
        )
        equations = f"""\
! {self.displayName}
EQUATIONS 2
Tcw = 1
{temperatureVariable} = Tcw

"""
        return equations, startingUnit

    def _setUnFlippedPortPos(self, delta: float) -> None:
        self.origOutputsPos = [[0, delta]]
        self._graphicalPortItem.setPos(self.origOutputsPos[0][0], self.origOutputsPos[0][1])
