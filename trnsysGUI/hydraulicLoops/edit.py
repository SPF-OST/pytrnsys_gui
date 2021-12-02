from __future__ import annotations

from . import model as _model
from .dialogs.edit import dialog as _gui, model as _gmodel


def edit(
        hydraulicLoop: _model.HydraulicLoop,
        hydraulicLoops: _model.HydraulicLoops,
        fluids: _model.Fluids) -> None:
    guiHydraulicLoop = _createGuiLoop(hydraulicLoop)

    occupiedNames = [l.name.value for l in hydraulicLoops.hydraulicLoops if l != hydraulicLoop]

    okedOrCancelled = _gui.HydraulicLoopDialog.showDialog(guiHydraulicLoop, occupiedNames, fluids)
    if okedOrCancelled == "cancelled":
        return

    _applyModel(guiHydraulicLoop, hydraulicLoop)


def _createGuiLoop(hydraulicLoop: _model.HydraulicLoop) -> _gmodel.HydraulicLoop:
    guiConnections = [
        _gmodel.Connection(c.displayName, c.diameterInCm, c.uValueInWPerM2K, c.lengthInM, c)
        for c in hydraulicLoop.connections
    ]
    guiLoop = _gmodel.HydraulicLoop(hydraulicLoop.name.value, hydraulicLoop.fluid, guiConnections)
    return guiLoop


def _applyModel(guiHydraulicLoop: _gmodel.HydraulicLoop, hydraulicLoop: _model.HydraulicLoop) -> None:
    oldName = hydraulicLoop.name.value
    newName = guiHydraulicLoop.name
    if oldName != newName:
        hydraulicLoop.name = _model.UserDefinedName(newName)

    hydraulicLoop.fluid = guiHydraulicLoop.fluid

    for model in guiHydraulicLoop.connections:
        connection = model.connection

        connection.setName(model.name)
        connection.diameterInCm = model.diameterInCm
        connection.uValueInWPerM2K = model.uValueInWPerM2K
        connection.lengthInM = model.lengthInM
