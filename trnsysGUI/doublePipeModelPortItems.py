import trnsysGUI.massFlowSolver.networkModel as _mfn


class ColdPortItem(_mfn.PortItem):
    def canOverlapWith(self, other: _mfn.PortItem):
        isCompatibleType = type(other) == _mfn.PortItem or isinstance(  # pylint: disable=unidiomatic-typecheck
            other, ColdPortItem
        )
        return super().canOverlapWith(other) and isCompatibleType


class HotPortItem(_mfn.PortItem):
    def canOverlapWith(self, other: _mfn.PortItem):
        isCompatibleType = type(other) == _mfn.PortItem or isinstance(  # pylint: disable=unidiomatic-typecheck
            other, HotPortItem
        )
        return super().canOverlapWith(other) and isCompatibleType
