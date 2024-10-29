import typing as _tp

import trnsysGUI.images as _img
import trnsysGUI.massFlowSolver.networkModel as _mfn
import trnsysGUI.temperatures as _temps

from . import _tapBase as _tb


class TapMains(_tb.TapBase):
    def __init__(self, trnsysType: str, editor, displayName: str) -> None:
        super().__init__(
            trnsysType, editor, _mfn.PortItemDirection.OUTPUT, displayName
        )

    @classmethod
    @_tp.override
    def hasDdckPlaceHolders(cls) -> bool:
        return False

    @classmethod
    @_tp.override
    def _getImageAccessor(
        cls,
    ) -> _img.SvgImageAccessor:  # pylint: disable=arguments-differ
        return _img.TAP_MAINS_SVG

    def _getCanonicalMassFlowRate(self) -> float:
        return self.massFlowRateInKgPerH

    def exportPipeAndTeeTypesForTemp(
        self, startingUnit: int
    ) -> _tp.Tuple[str, int]:
        temperatureVariable = _temps.getTemperatureVariableName(
            self.shallRenameOutputTemperaturesInHydraulicFile(),
            componentDisplayName=self.displayName,
            nodeName=self._modelTerminal.name,
        )
        equations = f"""\
! {self.displayName}
EQUATIONS 1
{temperatureVariable} = Tcw

"""
        return equations, startingUnit

    def _setUnFlippedPortPos(self, delta: int) -> None:
        self.origOutputsPos = [[0, delta]]
        self._graphicalPortItem.setPos(
            self.origOutputsPos[0][0], self.origOutputsPos[0][1]
        )
