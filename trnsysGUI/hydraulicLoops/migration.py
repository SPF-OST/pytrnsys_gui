import typing as _tp

import trnsysGUI.connection.singlePipeConnection as _spc
import trnsysGUI.singlePipePortItem as _spi
from . import _loopWideDefaults as _lwd
from . import search
from . import model as _model


def createLoops(
    connections: _tp.Sequence[_spc.SinglePipeConnection], fluid: _model.Fluid  # type: ignore[name-defined]
) -> _model.HydraulicLoops:
    loops = _model.HydraulicLoops([])

    todo = connections
    while todo:
        nextConnection = todo[0]
        assert isinstance(nextConnection.fromPort, _spi.SinglePipePortItem)

        reachableConnections = [*search.getReachableConnections(nextConnection.fromPort)]
        todo = [c for c in todo if c not in reachableConnections]

        name = loops.generateName()

        useLoopWideDefaults = True
        _lwd.resetConnectionPropertiesToLoopWideDefaults(reachableConnections, name.value)
        loop = _model.HydraulicLoop(name, fluid, useLoopWideDefaults, reachableConnections)

        loops.addLoop(loop)

    return loops
