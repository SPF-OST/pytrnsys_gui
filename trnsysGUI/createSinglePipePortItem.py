from __future__ import annotations

import typing as _tp

from trnsysGUI.hydraulicLoops import search

import trnsysGUI.singlePipePortItem as _spc

if _tp.TYPE_CHECKING:
    import trnsysGUI.BlockItem as _bi


def createSinglePipePortItem(
    name: str, parent: _bi.BlockItem
) -> _spc.SinglePipePortItem:
    return _spc.SinglePipePortItem(
        name, parent, search.getInternallyConnectedPortItems
    )
