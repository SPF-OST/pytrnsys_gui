# pylint: skip-file

import typing as _tp

import trnsysGUI.BlockItem as _bi
import trnsysGUI.createSinglePipePortItem as _cspi
import trnsysGUI.images as _img
import trnsysGUI.internalPiping as _ip
import trnsysGUI.massFlowSolver.networkModel as _mfn
import trnsysGUI.temperatures as _temps


class WTap_main(_bi.BlockItem, _ip.HasInternalPiping):
    def __init__(self, trnsysType, parent, **kwargs):
        super(WTap_main, self).__init__(trnsysType, parent, **kwargs)
        self.w = 40
        self.h = 40

        self.outputs.append(_cspi.createSinglePipePortItem("o", 0, self))

        outputPort = _mfn.PortItem("Out", _mfn.PortItemDirection.OUTPUT)
        self._modelSource = _mfn.Source(outputPort)

        self.changeSize()

    def getDisplayName(self) -> str:
        return self.displayName

    def hasDdckPlaceHolders(self) -> bool:
        return False

    def shallRenameOutputTemperaturesInHydraulicFile(self):
        return False

    def _getImageAccessor(self) -> _tp.Optional[_img.ImageAccessor]:
        return _img.W_TAP_MAIN_SVG

    def changeSize(self):
        w = self.w
        h = self.h

        """ Resize block function """
        delta = 20

        # Limit the block size:
        if h < 20:
            h = 20
        if w < 40:
            w = 40
        # center label:
        rect = self.label.boundingRect()
        lw, lh = rect.width(), rect.height()
        lx = (w - lw) / 2
        self.label.setPos(lx, h)

        self.origOutputsPos = [[0, delta]]
        self.outputs[0].setPos(self.origOutputsPos[0][0], self.origOutputsPos[0][1])

        self.updateFlipStateH(self.flippedH)
        self.updateFlipStateV(self.flippedV)

        self.outputs[0].side = (self.rotationN + 2 * self.flippedH) % 4

        return w, h

    def exportMassFlows(self):
        resStr = "Mfr" + self.displayName + " = 1000" + "\n"
        equationNr = 1
        return resStr, equationNr

    def getInternalPiping(self) -> _ip.InternalPiping:
        return _ip.InternalPiping([self._modelSource], {self._modelSource.portItem: self.outputs[0]})

    def exportPipeAndTeeTypesForTemp(self, startingUnit: int) -> _tp.Tuple[str, int]:
        temperatureVariable = _temps.getTemperatureVariableName(self, self._modelSource)
        equations = f"""\
! {self.displayName}
EQUATIONS 2
Tcw = 1
{temperatureVariable} = Tcw

"""
        return equations, startingUnit
