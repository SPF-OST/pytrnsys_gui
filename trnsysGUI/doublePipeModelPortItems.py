import trnsysGUI.massFlowSolver.networkModel as _mfn


class ColdPortItem(_mfn.PortItem):
    def canConnectTo(self, other: _mfn.PortItem):
        return super().canConnectTo(other) and not isinstance(other, HotPortItem)


class HotPortItem(_mfn.PortItem):
    def canConnectTo(self, other: _mfn.PortItem):
        return super().canConnectTo(other) and not isinstance(other, ColdPortItem)
