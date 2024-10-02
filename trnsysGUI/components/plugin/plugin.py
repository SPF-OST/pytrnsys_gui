from __future__ import annotations

import collections.abc as _cabc
import dataclasses as _dc
import abc as _abc
import typing as _tp

import trnsysGUI.internalPiping as _ip

from . import graphics as _graphics

if _tp.TYPE_CHECKING:
    import trnsysGUI.BlockItem as _bi
    import trnsysGUI.PortItemBase as _pib


@_dc.dataclass
class CreatedInternalPiping:
    inputPorts: _cabc.Sequence[_pib.PortItemBase]
    outputPorts: _cabc.Sequence[_pib.PortItemBase]
    internalPiping: _ip.InternalPiping

    @staticmethod
    def empty() -> CreatedInternalPiping:
        emptyCreatedInternalPiping = CreatedInternalPiping([], [], _ip.InternalPiping([], {}))
        return emptyCreatedInternalPiping


class AbstractInternalPipingFactory(_abc.ABC):
    @_abc.abstractmethod
    def createInternalPiping(self, blockItem: _bi.BlockItem) -> CreatedInternalPiping:
        raise NotImplementedError()


@_dc.dataclass
class Plugin:
    typeName: str
    baseDisplayName: str
    graphics: _graphics.Graphics
    internalPipingFactory: AbstractInternalPipingFactory
