import abc as _abc
from trnsysGUI.Node import Node
from trnsysGUI.SegmentItemBase import SegmentItemBase
from trnsysGUI.SinglePipeSegmentItem import SinglePipeSegmentItem
from trnsysGUI.DoublePipeSegmentItem import DoublePipeSegmentItem
from trnsysGUI.SinglePipePortItem import SinglePipePortItem
from trnsysGUI.DoublePipePortItem import DoublePipePortItem



class SegmentItemFactoryBase(_abc.ABC):
    @_abc.abstractmethod
    def createSegmentItem(self, startNode, endNode, parent) -> SegmentItemBase:
        raise NotImplementedError()


class SinglePipeSegmentItemFactory(SegmentItemFactoryBase):
    def createSegmentItem(self, startNode, endNode, parent) -> SinglePipeSegmentItem:
        # if not isinstance(startNode, SinglePipePortItem):
        #     raise ValueError("`fromPort' isn't a single pipe port item.")
        # if not isinstance(endNode, SinglePipePortItem):
        #     raise ValueError("`toPort' isn't a single pipe port item.")

        return SinglePipeSegmentItem(startNode, endNode, parent)


class DoublePipeSegmentItemFactory(SegmentItemFactoryBase):
    def createSegmentItem(self, startNode, endNode, parent) -> DoublePipeSegmentItem:
        # if not isinstance(startNode, DoublePipePortItem):
        #     raise ValueError("`fromPort' isn't a double pipe port item.")
        # if not isinstance(endNode, DoublePipePortItem):
        #     raise ValueError("`toPort' isn't a double pipe port item.")

        return DoublePipeSegmentItem(startNode, endNode, parent)
