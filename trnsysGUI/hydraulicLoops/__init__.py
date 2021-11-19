from __future__ import annotations

__all__ = ["edit", "merge"]

from . import model as _model
from ._editDialog import gui as _gui
from ._editDialog import model as _gmodel
from . import _merge


merge = _merge.merge


def edit(hydraulicLoop: _model.HydraulicLoop, fluids: _model.Fluids) -> None:  # type: ignore[name-defined]
    guiHydraulicLoop = _createGuiLoop(hydraulicLoop)

    okedOrCancelled = _gui.HydraulicLoopDialog.showDialog(guiHydraulicLoop, fluids)
    if okedOrCancelled == "cancelled":
        return

    _applyModel(guiHydraulicLoop)


def _createGuiLoop(hydraulicLoop: _model.HydraulicLoop) -> _gmodel.HydraulicLoop:
    guiConnections = [
        _gmodel.Connection(c.displayName, c.diameterInCm, c.uValueInWPerM2K, c.lengthInM, c)
        for c in hydraulicLoop.connections
    ]
    guiLoop = _gmodel.HydraulicLoop(hydraulicLoop.name.value, hydraulicLoop.fluid, guiConnections)
    return guiLoop


def _applyModel(hydraulicLoop: _gmodel.HydraulicLoop) -> None:
    for model in hydraulicLoop.connections:
        connection = model.connection

        connection.setName(model.name)
        connection.diameterInCm = model.diameterInCm
        connection.uValueInWPerM2K = model.uValueInWPerM2K
        connection.lengthInM = model.lengthInM
