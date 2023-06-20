from __future__ import annotations

import typing as _tp

import trnsysGUI.segments.node as _node
import trnsysGUI.segments.singlePipeSegmentItem as _spsi
import trnsysGUI.segments.segmentItemBase as _sib
import trnsysGUI.segments.segmentItemFactoryBase as _sif

if _tp.TYPE_CHECKING:
    import trnsysGUI.connection.singlePipeConnection as _spc


class SinglePipeSegmentItemFactory(_sif.SegmentItemFactoryBase):
    def __init__(self, singlePipeConnection: _spc.SinglePipeConnection) -> None:
        self._connection = singlePipeConnection

    def create(self, startNode: _node.Node, endNode: _node.Node) -> _sib.SegmentItemBase:  # type: ignore
        return _spsi.SinglePipeSegmentItem(startNode, endNode, self._connection)
