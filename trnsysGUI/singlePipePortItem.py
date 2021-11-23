import typing as _tp

import massFlowSolver as _mfs
import massFlowSolver.networkModel as _mfn
from trnsysGUI.PortItemBase import PortItemBase  # type: ignore[attr-defined]


class SinglePipePortItem(PortItemBase):
    def getConnectedRealNode(self, portItem: _mfn.PortItem) -> _tp.Optional[_mfn.RealNodeBase]:
        connection: _mfs.MassFlowNetworkContributorMixin = self.connectionList[0]

        connectionInternalPiping = connection.getInternalPiping()
        connectionStartingNodes = connectionInternalPiping.openLoopsStartingNodes

        assert len(connectionStartingNodes) == 1

        connectionSinglePort = connectionStartingNodes[0]
        return connectionSinglePort
