import typing as _tp

import trnsysGUI.connection.connectorsAndPipesExportHelpers as _ehelpers
import trnsysGUI.connection.hydraulicExport.common as _hecom
import trnsysGUI.images as _img
import trnsysGUI.massFlowSolver.networkModel as _mfn
import trnsysGUI.temperatures as _temps
from . import _tapBase


class Tap(_tapBase.TapBase):
    def __init__(self, trnsysType: str, editor, displayName: str) -> None:
        super().__init__(
            trnsysType, editor, _mfn.PortItemDirection.INPUT, displayName
        )

    @classmethod
    @_tp.override
    def hasDdckPlaceHolders(cls) -> bool:
        return True

    @classmethod
    @_tp.override
    def _getImageAccessor(
        cls,
    ) -> _img.SvgImageAccessor:  # pylint: disable=arguments-differ
        return _img.TAP_SVG

    def _getCanonicalMassFlowRate(self) -> float:
        return -self.massFlowRateInKgPerH

    def exportPipeAndTeeTypesForTemp(
        self, startingUnit: int
    ) -> _tp.Tuple[str, int]:
        fromAdjacentHasPiping = _hecom.getAdjacentConnection(
            self._graphicalPortItem
        )

        inputTemperature = _ehelpers.getTemperatureVariableName(
            fromAdjacentHasPiping.hasInternalPiping,
            fromAdjacentHasPiping.sharedPort,
            _mfn.PortItemType.STANDARD,
        )

        tapTemperature = _temps.getTemperatureVariableName(
            shallRenameOutputInHydraulicFile=False,
            componentDisplayName=self.displayName,
            nodeName=self._modelTerminal.name,
        )

        equation = f"""\
EQUATIONS 1
{tapTemperature} = {inputTemperature}

"""
        return equation, startingUnit

    def _setUnFlippedPortPos(self, delta: int) -> None:
        self.origInputsPos = [[0, delta]]
        self._graphicalPortItem.setPos(
            self.origInputsPos[0][0], self.origInputsPos[0][1]
        )
