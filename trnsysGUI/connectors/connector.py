import typing as _tp

import trnsysGUI.BlockItem as _bi
import trnsysGUI.connectorsAndPipesExportHelpers as _helpers
import trnsysGUI.createSinglePipePortItem as _cspi
import trnsysGUI.images as _img
import trnsysGUI.internalPiping as _ip
import trnsysGUI.massFlowSolver.networkModel as _mfn
import trnsysGUI.temperatures as _temps


class Connector(_bi.BlockItem, _ip.HasInternalPiping):
    def __init__(self, trnsysType, parent, **kwargs):
        super().__init__(trnsysType, parent, **kwargs)

        self.sizeFactor = 0.5
        self.w = 40
        self.h = 40

        self.inputs.append(_cspi.createSinglePipePortItem("i", 0, self))
        self.outputs.append(_cspi.createSinglePipePortItem("o", 2, self))

        self._updateModels(self.displayName)

        self.changeSize()

    def getDisplayName(self) -> str:
        return self.displayName

    def hasDdckPlaceHolders(self) -> bool:
        return False

    def shallRenameOutputTemperaturesInHydraulicFile(self):
        return False

    def getInternalPiping(self) -> _ip.InternalPiping:
        return _ip.InternalPiping(
            [self._modelPipe], {self._modelPipe.fromPort: self.inputs[0], self._modelPipe.toPort: self.outputs[0]}
        )

    def _getImageAccessor(self) -> _tp.Optional[_img.ImageAccessor]:
        return _img.CONNECTOR_PNG

    def _updateModels(self, newDisplayName: str) -> None:
        fromPort = _mfn.PortItem("In", _mfn.PortItemDirection.INPUT)
        toPort = _mfn.PortItem("Out", _mfn.PortItemDirection.OUTPUT)
        self._modelPipe = _mfn.Pipe(fromPort, toPort)

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

    def exportPipeAndTeeTypesForTemp(self, startingUnit: int) -> _tp.Tuple[str, int]:
        tempName = _temps.getTemperatureVariableName(self, self._modelPipe)
        mfrName = _helpers.getInputMfrName(self, self._modelPipe)

        fromConnection = self.inputs[0].getConnection()
        toConnection = self.outputs[0].getConnection()

        posFlowTempName = _helpers.getTemperatureVariableName(fromConnection, self.inputs[0], _mfn.PortItemType.STANDARD)
        negFlowTempName = _helpers.getTemperatureVariableName(toConnection, self.outputs[0], _mfn.PortItemType.STANDARD)

        unitNumber = startingUnit
        unitText = _helpers.getIfThenElseUnit(unitNumber, tempName, mfrName, posFlowTempName, negFlowTempName)

        nextUnitNumber = unitNumber + 1

        return unitText, nextUnitNumber
