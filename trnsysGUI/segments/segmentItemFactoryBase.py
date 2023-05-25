import abc as _abc

import trnsysGUI.segments.Node as _node
import trnsysGUI.segments.segmentItemBase as _sib


class SegmentItemFactoryBase(_abc.ABC):
    @_abc.abstractmethod
    def create(self, startNode: _node.Node, endNode: _node.Node) -> _sib.SegmentItemBase:
        raise NotImplementedError()
