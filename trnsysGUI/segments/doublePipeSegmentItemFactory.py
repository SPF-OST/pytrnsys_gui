from __future__ import annotations

import typing as _tp

import trnsysGUI.segments.Node as _node
import trnsysGUI.segments.doublePipeSegmentItem as _dpsi
import trnsysGUI.segments.segmentItemBase as _sib
import trnsysGUI.segments.segmentItemFactoryBase as _sif

if _tp.TYPE_CHECKING:
    import trnsysGUI.connection.doublePipeConnection as _dpc


class DoublePipeSegmentItemFactory(_sif.SegmentItemFactoryBase):
    def __init__(self, doublePipeConnection: _dpc.DoublePipeConnection) -> None:
        self._connection = doublePipeConnection

    def create(self, startNode: _node.Node, endNode: _node.Node) -> _sib.SegmentItemBase:  # type: ignore
        return _dpsi.DoublePipeSegmentItem(startNode, endNode, self._connection)