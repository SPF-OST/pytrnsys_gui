import typing as _tp

import trnsysGUI.BlockItem as _bi
import trnsysGUI.internalPiping as _ip


class BlockItemHasInternalPiping(_bi.BlockItem, _ip.HasInternalPiping):
    @_tp.override
    def getDisplayName(self) -> str:
        raise NotImplementedError()

    def getInternalPiping(self) -> _ip.InternalPiping:
        raise NotImplementedError()
