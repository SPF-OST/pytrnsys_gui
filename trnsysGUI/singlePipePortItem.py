import typing as _tp

import massFlowSolver as _mfs
import massFlowSolver.networkModel as _mfn
import massFlowSolver.search as _search
from trnsysGUI.PortItemBase import PortItemBase  # type: ignore[attr-defined]


class SinglePipePortItem(PortItemBase):
    def _selectConnectedRealNode(  # pylint: disable=duplicate-code  # 2
        self,
        portItem: _mfn.PortItem,
        connectedPortItemsAndAdjacentRealNode: _tp.Sequence[_mfs.PortItemAndAdjacentRealNode],
    ) -> _mfn.RealNodeBase:
        assert (
            len(connectedPortItemsAndAdjacentRealNode) == 1
        ), "Only exactly one model port item should be connected with a single pipe graphical port item."

        selectedRealNode = connectedPortItemsAndAdjacentRealNode[0].realNode

        return selectedRealNode

    def _highlightInternallyConnectedPortItems(self):
        internallyConnectedPortItems = list(_search.getInternallyConnectedPortItems(self))
        for portItem in internallyConnectedPortItems:
            portItem.innerCircle.setBrush(self.ashColorB)

    def _unhighlightInternallyConnectedPortItems(self):
        internallyConnectedPortItems = list(_search.getInternallyConnectedPortItems(self))
        for portItem in internallyConnectedPortItems:
            portItem.innerCircle.setBrush(self.visibleColor)
