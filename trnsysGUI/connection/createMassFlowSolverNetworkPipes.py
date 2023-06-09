import typing as _tp

from trnsysGUI.massFlowSolver import networkModel as _mfn


def createMassFlowSolverNetworkPipes() -> _tp.Tuple[_mfn.Pipe, _mfn.Pipe]:
    coldInput = _mfn.PortItem("In", _mfn.PortItemDirection.INPUT, _mfn.PortItemType.COLD)
    coldOutput = _mfn.PortItem("Out", _mfn.PortItemDirection.OUTPUT, _mfn.PortItemType.COLD)
    coldPipe = _mfn.Pipe(coldInput, coldOutput, "Cold")

    hotInput = _mfn.PortItem("In", _mfn.PortItemDirection.INPUT, _mfn.PortItemType.HOT)
    hotOutput = _mfn.PortItem("Out", _mfn.PortItemDirection.OUTPUT, _mfn.PortItemType.HOT)
    hotPipe = _mfn.Pipe(hotInput, hotOutput, "Hot")

    return coldPipe, hotPipe
