import typing as _tp

import massFlowSolver as _mfs
import massFlowSolver.networkModel as _mfn
from trnsysGUI.PortItemBase import PortItemBase  # type: ignore[attr-defined]
from trnsysGUI.modelPortItems import ColdPortItem, HotPortItem


class DoublePipePortItem(PortItemBase):
    def getConnectedRealNode(self, portItem: _mfn.PortItem) -> _tp.Optional[_mfn.RealNodeBase]:
        connection: _mfs.MassFlowNetworkContributorMixin = self.connectionList[0]

        connectionInternalPiping = connection.getInternalPiping()
        connectionStartingNodes = connectionInternalPiping.openLoopsStartingNodes

        assert len(connectionStartingNodes) == 2
        connectionColdPort = connectionStartingNodes[0]
        connectionHotPort = connectionStartingNodes[1]

        if isinstance(portItem, ColdPortItem):
            return connectionColdPort
        if isinstance(portItem, HotPortItem):
            return connectionHotPort

        raise AssertionError("portItem is not valid DoublePipePortItem")
