import typing as _tp

import trnsysGUI.BlockItem as _bi
import trnsysGUI.PortItemBase as _pib
import trnsysGUI.internalPiping as _ip


class TeePieceBase(_bi.BlockItem, _ip.HasInternalPiping):
    def __init__(self, trnsysType: str, editor, displayName: str) -> None:
        super().__init__(trnsysType, editor, displayName)

        self.h = 40
        self.w = 40

        inputPort, outputPort1, outputPort2 = self._createInputAndOutputPorts()

        self.inputs.append(inputPort)

        self.outputs.append(outputPort1)
        self.outputs.append(outputPort2)

    def _createInputAndOutputPorts(self) -> _tp.Tuple[_pib.PortItemBase, _pib.PortItemBase, _pib.PortItemBase]:
        raise NotImplementedError()

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
        raise NotImplementedError()

    def exportPipeAndTeeTypesForTemp(self, startingUnit: int) -> _tp.Tuple[str, int]:
        raise NotImplementedError()

    def changeSize(self):
        self._positionLabel()

        width, _ = self._getCappedWidthAndHeight()

        self.origInputsPos = [[0, self._portOffset]]
        self.origOutputsPos = [[width, self._portOffset], [self._portOffset, 0]]

        self.inputs[0].setPos(self.origInputsPos[0][0], self.origInputsPos[0][1])
        self.outputs[0].setPos(self.origOutputsPos[0][0], self.origOutputsPos[0][1])
        self.outputs[1].setPos(self.origOutputsPos[1][0], self.origOutputsPos[1][1])

        self.updateFlipStateH(self.flippedH)
        self.updateFlipStateV(self.flippedV)

        self.inputs[0].side = (self.rotationN + 2 * self.flippedH) % 4
        self.outputs[0].side = (self.rotationN + 2 - 2 * self.flippedH) % 4
        self.outputs[1].side = (self.rotationN + 1 - 2 * self.flippedV) % 4

    @property
    def _portOffset(self) -> int:
        raise NotImplementedError()
