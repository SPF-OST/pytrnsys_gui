import typing as _tp

import trnsysGUI.PortItemBase as _pi
import trnsysGUI.doublePipeModelPortItems as _dpmpi
import trnsysGUI.massFlowSolver as _mfs
import trnsysGUI.massFlowSolver.networkModel as _mfn


class DoublePipePortItem(_pi.PortItemBase):
    def _selectConnectedRealNode(  # pylint: disable=duplicate-code  # 1
            self,
            portItem: _mfn.PortItem,
            connectedPortItemsAndAdjacentRealNode: _tp.Sequence[_mfs.PortItemAndAdjacentRealNode],
    ) -> _mfn.RealNodeBase:
        assert isinstance(
            portItem, (_dpmpi.ColdPortItem, _dpmpi.HotPortItem)
        ), "Only hot or cold model port items should be mapped to double pipe graphical port items."

        selectedRealNodes = [
            pan.realNode
            for pan in connectedPortItemsAndAdjacentRealNode
            if type(pan.portItem) == type(portItem)  # pylint: disable=unidiomatic-typecheck
        ]

        assert (
                len(selectedRealNodes) == 1
        ), "Only exactly one hot (or cold) model port item should be connected to a double pipe graphical port item."

        selectedRealNode = selectedRealNodes[0]

        return selectedRealNode

    def _highlightInternallyConnectedPortItems(self):
        pass

    def _unhighlightInternallyConnectedPortItems(self):
        pass
