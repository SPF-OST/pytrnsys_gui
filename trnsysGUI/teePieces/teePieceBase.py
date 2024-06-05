import typing as _tp

import trnsysGUI.PortItemBase as _pib
import trnsysGUI.blockItemGraphicItemMixins as _gimx
import trnsysGUI.blockItemHasInternalPiping as _bip
import trnsysGUI.images as _img
import trnsysGUI.internalPiping as _ip
import trnsysGUI.teePieces.teePieceBaseModel as _tpbm


class TeePieceBase(_bip.BlockItemHasInternalPiping, _gimx.SvgBlockItemGraphicItemMixin):
    def __init__(self, trnsysType: str, editor, displayName: str) -> None:
        super().__init__(trnsysType, editor, displayName)

        self.h = 40
        self.w = 40

        inputPort, outputPort1, outputPort2 = self._createInputAndOutputPorts()

        self.inputs.append(inputPort)

        self.outputs.append(outputPort1)
        self.outputs.append(outputPort2)

    @classmethod
    @_tp.override
    def _getImageAccessor(cls) -> _img.SvgImageAccessor:  # pylint: disable=arguments-differ
        raise NotImplementedError()

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

    def _encodeTeePieceBaseModel(self) -> _tpbm.TeePieceBaseModel:
        blockItemModel = self._encodeBaseModel()

        inputPortId = self.inputs[0].id
        outputPortIds = (self.outputs[0].id, self.outputs[1].id)

        baseModel = _tpbm.TeePieceBaseModel(
            blockItemModel,
            inputPortId,
            outputPortIds,
        )

        return baseModel

    def _decodeTeePieceBaseModel(self, baseModel: _tpbm.TeePieceBaseModel) -> None:
        self.inputs[0].id = baseModel.inputPortId

        self.outputs[0].id = baseModel.outputPortIds[0]
        self.outputs[1].id = baseModel.outputPortIds[1]

        self._decodeBaseModel(baseModel.blockItemModel)

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
