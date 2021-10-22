# pylint: skip-file
# type: ignore

import abc as _abc

from trnsysGUI.DoublePipeSegmentItem import DoublePipeSegmentItem
from trnsysGUI.SegmentItemBase import SegmentItemBase
from trnsysGUI.SinglePipeSegmentItem import SinglePipeSegmentItem


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
