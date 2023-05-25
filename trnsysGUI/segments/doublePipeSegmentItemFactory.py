import trnsysGUI.segments.doublePipeSegmentItem as _dpsi
import trnsysGUI.segments.segmentItemBase as _sib

import trnsysGUI.segments.Node as _node

import trnsysGUI.segments.segmentItemFactoryBase as _sif

import trnsysGUI.connection.doublePipeConnection as _dpc


class DoublePipeSegmentItemFactory(_sif.SegmentItemFactoryBase):
    def __init__(self, doublePipeConnection: _dpc.DoublePipeConnection) -> None:
        self._connection = doublePipeConnection

    def create(self, startNode: _node.Node, endNode: _node.Node) -> _sib.SegmentItemBase:
        return _dpsi.DoublePipeSegmentItem(startNode, endNode, self._connection)
