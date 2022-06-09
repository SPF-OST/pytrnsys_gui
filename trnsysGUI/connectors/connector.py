import typing as _tp

import trnsysGUI.createSinglePipePortItem as _cspi
import trnsysGUI.images as _img
import trnsysGUI.BlockItem as _bi
import trnsysGUI.massFlowSolver as _mfs
import trnsysGUI.massFlowSolver.networkModel as _mfn

import trnsysGUI.connectorsAndPipesExportHelpers as _helpers


class Connector(_bi.BlockItem, _mfs.MassFlowNetworkContributorMixin):
    def __init__(self, trnsysType, parent, **kwargs):
        super().__init__(trnsysType, parent, **kwargs)

        self._updateModelPipe(self.displayName)

        self.sizeFactor = 0.5
        self.w = 40
        self.h = 40

        self.inputs.append(_cspi.createSinglePipePortItem("i", 0, self))
        self.outputs.append(_cspi.createSinglePipePortItem("o", 2, self))

        self.changeSize()

    def getInternalPiping(self) -> _mfs.InternalPiping:
        return _mfs.InternalPiping(
            [self._modelPipe], {self._modelPipe.fromPort: self.inputs[0], self._modelPipe.toPort: self.outputs[0]}
        )

    def _getImageAccessor(self) -> _tp.Optional[_img.ImageAccessor]:
        return _img.CONNECTOR_PNG

    def setDisplayName(self, newName: str) -> None:
        super().setDisplayName(newName)
        self._updateModelPipe(newName)

    def changeSize(self):
        width = self.w
        height = self.h

        delta = 20  # pylint: disable=duplicate-code  # 1
        # Limit the block size:
        height = max(height, 20)
        width = max(width, 40)

        # center label:
        rect = self.label.boundingRect()
        labelWidth = rect.width()  # pylint: disable=duplicate-code  # 1
        labelPosX = (width - labelWidth) / 2
        self.label.setPos(labelPosX, height)

        self.origInputsPos = [[0, delta]]
        self.origOutputsPos = [[width, delta]]  # pylint: disable=duplicate-code  # 1
        self.inputs[0].setPos(self.origInputsPos[0][0], self.origInputsPos[0][1])
        self.outputs[0].setPos(self.origOutputsPos[0][0], self.origOutputsPos[0][1])

        self.updateFlipStateH(self.flippedH)
        self.updateFlipStateV(self.flippedV)

        self.inputs[0].side = (self.rotationN + 2 * self.flippedH) % 4
        self.outputs[0].side = (self.rotationN + 2 - 2 * self.flippedH) % 4  # pylint: disable=duplicate-code  # 1

        return width, height

    def exportBlackBox(self):
        return "noBlackBoxOutput", []

    def exportPipeAndTeeTypesForTemp(self, startingUnit: int) -> _tp.Tuple[str, int]:
        tempName = self.getTemperatureVariableName(self.inputs[0])
        mfrName = _helpers.getMfrName(self._modelPipe)

        fromConnection = self.inputs[0].getConnection()
        toConnection = self.outputs[0].getConnection()

        posFlowTempName = f"T{fromConnection.displayName}"
        negFlowTempName = f"T{toConnection.displayname}"
        equation = f"{tempName} = GE({mfrName}, 0)*{posFlowTempName} + LT({mfrName}, 0)*{negFlowTempName}"
        equations = f"""\
EQUATIONS 1
{equation}
"""
        return equations, startingUnit

    def _updateModelPipe(self, displayName: str) -> None:
        fromPort = _mfn.PortItem("input", _mfn.PortItemType.INPUT)
        toPort = _mfn.PortItem("output", _mfn.PortItemType.OUTPUT)
        self._modelPipe = _mfn.Pipe(displayName, self.trnsysId, fromPort, toPort)
