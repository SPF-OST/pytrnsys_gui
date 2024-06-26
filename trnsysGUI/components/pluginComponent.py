import typing as _tp

import pytrnsys.utils.result as _res

import trnsysGUI.blockItemGraphicItemMixins as _gimx
import trnsysGUI.blockItemHasInternalPiping as _bip
import trnsysGUI.images as _img
import trnsysGUI.internalPiping as _ip

from .plugin import factory as _factory


class PluginComponentCreationError(Exception):
    pass


class PluginComponent(_bip.BlockItemHasInternalPiping, _gimx.SvgBlockItemGraphicItemMixin):
    def __init__(self, trnsysType: str, editor, displayName: str) -> None:
        super().__init__(trnsysType, editor, displayName)

        factory = _factory.Factory.createDefault()
        pluginResult = factory.create(trnsysType)

        if _res.isError(pluginResult):
            errorMessage = _res.error(pluginResult).message
            raise PluginComponentCreationError(errorMessage)
        plugin = _res.value(pluginResult)

        createdInternalPiping = plugin.internalPipingFactory.createInternalPiping(self)

        self.inputs.extend(createdInternalPiping.inputPorts)
        self.outputs.extend(createdInternalPiping.outputPorts)
        self._internalPiping = createdInternalPiping.internalPiping

        self._imageAccessor = plugin.graphics.accessor
        self.w = plugin.graphics.size.width
        self.h = plugin.graphics.size.height

        self.changeSize()

    def getDisplayName(self) -> str:
        return self.displayName

    @_tp.override
    def _getImageAccessor(self) -> _img.SvgImageAccessor:
        return self._imageAccessor

    def getInternalPiping(self) -> _ip.InternalPiping:
        return self._internalPiping
