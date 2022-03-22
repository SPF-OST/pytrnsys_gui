from __future__ import annotations

import typing as _tp

import trnsysGUI.PortItemBase as _pi
import trnsysGUI.massFlowSolver as _mfs
import trnsysGUI.massFlowSolver.networkModel as _mfn

if _tp.TYPE_CHECKING:
    import trnsysGUI.BlockItem as _bi

GetInternallyConnectedPortItems = _tp.Callable[["SinglePipePortItem"], _tp.Sequence["SinglePipePortItem"]]
Side = _tp.Literal[0, 2]


class SinglePipePortItem(_pi.PortItemBase):
    def __init__(
            self,
            name: str,
            side: Side,
            parent: _bi.BlockItem,
            getInternallyConnectedPortItems: GetInternallyConnectedPortItems,
    ) -> None:
        super().__init__(name, side, parent)

        self._getInternallyConnectedPortItems = getInternallyConnectedPortItems

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
        for portItem in self._getInternallyConnectedPortItems(self):
            portItem.innerCircle.setBrush(self.ashColorB)

    def _unhighlightInternallyConnectedPortItems(self):
        for portItem in self._getInternallyConnectedPortItems(self):
            portItem.innerCircle.setBrush(self.visibleColor)
