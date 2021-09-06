# pylint: skip-file

from __future__ import annotations

__all__ = ["getOrCreateHydraulicLoop", "showHydraulicLoopDialog"]

import trnsysGUI.PortItem as _pi

from . import _gui
from . import _model


def getOrCreateHydraulicLoop(
    fromPort: _pi.PortItem, toPort: _pi.PortItem  # type: ignore[name-defined]
) -> "_model.HydraulicLoop":
    connections = [
        _model.Connection("conn1", 10.0, None),
        _model.Connection("conn2", 10.0, None),
        _model.Connection("conn3", 3.0, None),
        _model.Connection("conn4", 10.0, None),
        _model.Connection("conn5", 10.0, None),
        _model.Connection("conn6", 10.0, None),
    ]

    fluid = _model.Fluid("water", 4184.0)

    return _model.HydraulicLoop("loop", fluid, connections)


def showHydraulicLoopDialog(
    fromPort: _pi.PortItem, toPort: _pi.PortItem  # type: ignore[name-defined]
) -> None:
    hydraulicLoop = getOrCreateHydraulicLoop(fromPort, toPort)
    _gui.HydraulicLoopDialog.showDialog(hydraulicLoop)
    _applyModel(hydraulicLoop)


def _applyModel(hydraulicLoop: _model.HydraulicLoop) -> None:
    pass
