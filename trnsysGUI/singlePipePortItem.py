import typing as _tp

import massFlowSolver as _mfs
import massFlowSolver.networkModel as _mfn
from trnsysGUI.PortItemBase import PortItemBase  # type: ignore[attr-defined]


class SinglePipePortItem(PortItemBase):
    def _selectConnectedRealNode(  # pylint: disable=duplicate-code  # 2
        self,
        portItem: _mfn.PortItem,
        connectedPortItemsAndAdjacentRealNode: _tp.Sequence[_mfs.PortItemAndAdjacentRealNode],
    ) -> _mfn.RealNodeBase:
        assert (
            len(connectedPortItemsAndAdjacentRealNode) == 1
        ), "Only exactly one model port item can should connected with a single pipe graphical port item."

        selectedRealNode = connectedPortItemsAndAdjacentRealNode[0].realNode

        return selectedRealNode
