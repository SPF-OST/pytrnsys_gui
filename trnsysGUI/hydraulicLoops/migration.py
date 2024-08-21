import typing as _tp

import trnsysGUI.connection.singlePipeConnection as _spc
import trnsysGUI.singlePipePortItem as _spi
from . import _setConnectionProperties as _scp
from . import connectionsDefinitionMode as _cdm
from . import model as _model
from . import search


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

        connectionsDefinitionMode = _cdm.ConnectionsDefinitionMode.LOOP_WIDE_DEFAULTS
        _scp.setConnectionPropertiesForDefinitionMode(reachableConnections, name.value, connectionsDefinitionMode)
        loop = _model.HydraulicLoop(name, fluid, connectionsDefinitionMode, reachableConnections)

        loops.addLoop(loop)

    return loops
