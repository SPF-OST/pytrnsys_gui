import typing as _tp

import trnsysGUI.connection.singlePipeConnection as _spc
import trnsysGUI.massFlowSolver.search as _search
import trnsysGUI.singlePipePortItem as _spi
from . import model as _model


def createLoops(
    connections: _tp.Sequence[_spc.SinglePipeConnection], fluid: _model.Fluid  # type: ignore[name-defined]
) -> _model.HydraulicLoops:
    loops = _model.HydraulicLoops([])

    todo = connections
    while todo:
        nextConnection = todo[0]
        assert isinstance(nextConnection.fromPort, _spi.SinglePipePortItem)

        reachableConnections = [*_search.getReachableConnections(nextConnection.fromPort)]
        todo = [c for c in todo if c not in reachableConnections]

        name = loops.generateName()

        useLoopWideDefaults = False
        loop = _model.HydraulicLoop(name, fluid, useLoopWideDefaults, reachableConnections)

        loops.addLoop(loop)

    return loops
