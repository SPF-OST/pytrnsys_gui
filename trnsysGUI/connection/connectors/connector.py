import typing as _tp

import trnsysGUI.BlockItem as _bi
import trnsysGUI.connection.hydraulicExport.singlePipe.createExportHydraulicSinglePipeConnection as _cehspc
import trnsysGUI.createSinglePipePortItem as _cspi
import trnsysGUI.images as _img
import trnsysGUI.internalPiping as _ip
import trnsysGUI.massFlowSolver.networkModel as _mfn


class Connector(_bi.BlockItem, _ip.HasInternalPiping):  # pylint: disable=too-many-instance-attributes
    def __init__(self, trnsysType: str, editor, displayName: str) -> None:
        super().__init__(trnsysType, editor, displayName)

        self.sizeFactor = 0.5
        self.w = 40
        self.h = 40

        self.fromPort = _cspi.createSinglePipePortItem("i", 0, self)
        self.toPort = _cspi.createSinglePipePortItem("o", 2, self)

        self.inputs.append(self.fromPort)
        self.outputs.append(self.toPort)

        self._setModels()

        self.changeSize()

    def getDisplayName(self) -> str:
        return self.displayName

    @classmethod
    @_tp.override
    def hasDdckPlaceHolders(cls) -> bool:
        return False

    @classmethod
    @_tp.override
    def shallRenameOutputTemperaturesInHydraulicFile(cls) -> bool:
        return False

    def getInternalPiping(self) -> _ip.InternalPiping:
        return _ip.InternalPiping(
            [self._modelPipe], {self._modelPipe.fromPort: self.inputs[0], self._modelPipe.toPort: self.outputs[0]}
        )

    def _getImageAccessor(self) -> _tp.Optional[_img.ImageAccessor]:
        return _img.CONNECTOR_SVG

    def _setModels(self) -> None:
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
        return _cehspc.exportDummySinglePipeConnection(self, startingUnit, self.fromPort, self.toPort, self._modelPipe)
