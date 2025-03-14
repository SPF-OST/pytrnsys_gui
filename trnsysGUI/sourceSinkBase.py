import pathlib as _pl
import typing as _tp

import trnsysGUI.blockItemGraphicItemMixins as _gimx
import trnsysGUI.blockItemHasInternalPiping as _bip
import trnsysGUI.createSinglePipePortItem as _cspi
import trnsysGUI.images as _img
import trnsysGUI.internalPiping as _ip
import trnsysGUI.massFlowSolver.networkModel as _mfn


class SourceSinkBase(
    _bip.BlockItemHasInternalPiping, _gimx.SvgBlockItemGraphicItemMixin
):
    def __init__(self, trnsysType: str, editor, displayName: str) -> None:
        super().__init__(trnsysType, editor, displayName)

        self.w = 60
        self.h = 60

        self.massFlowRateInKgPerH = 500

        self.inputs.append(_cspi.createSinglePipePortItem("i", self))
        self.outputs.append(_cspi.createSinglePipePortItem("o", self))

        self.changeSize()

        self._updateDdckFilePath()

    def getDisplayName(self) -> str:
        return self.displayName

    def setDisplayName(self, newName: str) -> None:
        super().setDisplayName(newName)
        self._updateDdckFilePath()

    def _updateDdckFilePath(self):
        ddckFilePath = (
            _pl.Path(self.editor.projectFolder)
            / "ddck"
            / f"{self.displayName}.ddck"
        )
        self.path = str(ddckFilePath)

    @classmethod
    @_tp.override
    def _getImageAccessor(  # pylint: disable=arguments-differ
        cls,
    ) -> _img.SvgImageAccessor:
        raise NotImplementedError()

    @classmethod
    def _getInputAndOutputXPos(cls) -> tuple[int, int]:
        raise NotImplementedError()

    def changeSize(self):
        self._positionLabel()

        inputX, outputX = self._getInputAndOutputXPos()

        self.inputs[0].setPos(inputX, 0)
        self.outputs[0].setPos(outputX, 0)

        self.updateFlipStateH(self.flippedH)
        self.updateFlipStateV(self.flippedV)

    def getInternalPiping(self) -> _ip.InternalPiping:
        inputPort = _mfn.PortItem("In", _mfn.PortItemDirection.INPUT)
        outputPort = _mfn.PortItem("Out", _mfn.PortItemDirection.OUTPUT)
        pump = _mfn.Pump(inputPort, outputPort)

        modelPortItemsToGraphicalPortItem = {
            inputPort: self.inputs[0],
            outputPort: self.outputs[0],
        }
        return _ip.InternalPiping([pump], modelPortItemsToGraphicalPortItem)

    def exportMassFlows(self):
        equationNr = 1
        massFlowLine = f"Mfr{self.displayName} = {self.massFlowRateInKgPerH}\n"
        return massFlowLine, equationNr
