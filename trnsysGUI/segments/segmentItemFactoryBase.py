from __future__ import annotations

import abc as _abc

import trnsysGUI.segments.node as _node
import trnsysGUI.segments.segmentItemBase as _sib


class SegmentItemFactoryBase(_abc.ABC):
    @_abc.abstractmethod
    def create(
        self, startNode: _node.Node, endNode: _node.Node  # type: ignore
    ) -> _sib.SegmentItemBase:  # type: ignore
        raise NotImplementedError()
