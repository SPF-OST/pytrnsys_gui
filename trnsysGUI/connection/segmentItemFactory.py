import abc as _abc

from trnsysGUI.doublePipeSegmentItem import DoublePipeSegmentItem
from trnsysGUI.SegmentItemBase import SegmentItemBase  # type: ignore[attr-defined]
from trnsysGUI.singlePipeSegmentItem import SinglePipeSegmentItem


class SegmentItemFactoryBase(_abc.ABC):
    @_abc.abstractmethod
    def createSegmentItem(self, startNode, endNode, parent) -> SegmentItemBase:
        raise NotImplementedError()


class SinglePipeSegmentItemFactory(SegmentItemFactoryBase):
    def createSegmentItem(self, startNode, endNode, parent) -> SinglePipeSegmentItem:
        return SinglePipeSegmentItem(startNode, endNode, parent)


class DoublePipeSegmentItemFactory(SegmentItemFactoryBase):
    def createSegmentItem(self, startNode, endNode, parent) -> DoublePipeSegmentItem:
        return DoublePipeSegmentItem(startNode, endNode, parent)
