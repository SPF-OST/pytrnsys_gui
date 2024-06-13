import pathlib as _pl
import typing as _tp

import trnsysGUI.blockItemGraphicItemMixins as _gimx
import trnsysGUI.blockItemHasInternalPiping as _bip
import trnsysGUI.images as _img
import trnsysGUI.internalPiping as _ip

from .plugin import factory as _factory


class PluginComponent(_bip.BlockItemHasInternalPiping, _gimx.SvgBlockItemGraphicItemMixin):
    def __init__(self, trnsysType: str, editor, displayName: str) -> None:
        super().__init__(trnsysType, editor, displayName)

        factory = _factory.Factory.createDefault()
        plugin = factory.createOrNone(trnsysType)

        createdInternalPiping = plugin.internalPipingFactory.createInternalPiping(self)

        self.inputs = createdInternalPiping.inputPorts
        self.outputs = createdInternalPiping.outputPorts
        self._internalPiping = createdInternalPiping.internalPiping

        self._imageAccessor = plugin.graphics.accessor
        self.w = plugin.graphics.size.width
        self.h = plugin.graphics.size.height

        self.changeSize()

        self._updateDdckFilePath()

    def getDisplayName(self) -> str:
        return self.displayName

    def setDisplayName(self, newName: str) -> None:
        super().setDisplayName(newName)
        self._updateDdckFilePath()

    def _updateDdckFilePath(self):
        ddckFilePath = _pl.Path(self.editor.projectFolder) / "ddck" / f"{self.displayName}.ddck"
        self.path = str(ddckFilePath)

    @_tp.override
    def _getImageAccessor(self) -> _img.SvgImageAccessor:
        return self._imageAccessor

    def getInternalPiping(self) -> _ip.InternalPiping:
        return self._internalPiping
