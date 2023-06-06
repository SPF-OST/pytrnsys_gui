import typing as _tp

import trnsysGUI.connection.hydraulicExport.doublePipe.dummy as _dummy
from . import _simulated as _sim
from . import doublePipeConnection as _dpc


def export(doublePipeConnection: _dpc.DoublePipeConnection, unitNumber: int) -> _tp.Tuple[str, int]:
    if doublePipeConnection.shallBeSimulated:
        return _sim.exportSimulatedConnection(doublePipeConnection, unitNumber)

    hydraulicConnection = doublePipeConnection.hydraulicConnection
    return _dummy.exportDummyConnection(hydraulicConnection, unitNumber)
