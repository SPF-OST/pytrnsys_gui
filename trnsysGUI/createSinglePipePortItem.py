from __future__ import annotations

import typing as _tp

import trnsysGUI.singlePipePortItem as _spc
import trnsysGUI.massFlowSolver.search as _search

if _tp.TYPE_CHECKING:
    import trnsysGUI.BlockItem as _bi


def createSinglePipePortItem(
    name: str, side: _spc.Side, parent: _bi.BlockItem  # type: ignore[name-defined]
) -> _spc.SinglePipePortItem:
    return _spc.SinglePipePortItem(name, side, parent, _search.getInternallyConnectedPortItems)