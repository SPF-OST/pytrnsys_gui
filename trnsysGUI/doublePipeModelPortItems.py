import trnsysGUI.massFlowSolver.networkModel as _mfn


class ColdPortItem(_mfn.PortItem):
    def canOverlapWith(self, other: _mfn.PortItem):
        return super().canOverlapWith(other) and not isinstance(other, HotPortItem)


class HotPortItem(_mfn.PortItem):
    def canOverlapWith(self, other: _mfn.PortItem):
        return super().canOverlapWith(other) and not isinstance(other, ColdPortItem)
