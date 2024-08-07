from __future__ import annotations

import trnsysGUI.connection.singlePipeDefaultValues as _defaults

from . import _loopWideDefaults as _lwd
from . import common as _common
from . import model as _model
from ._dialogs.edit import dialog as _gui, model as _gmodel


def edit(hydraulicLoop: _model.HydraulicLoop, hydraulicLoops: _model.HydraulicLoops, fluids: _model.Fluids) -> None:
    guiHydraulicLoop = _createGuiLoop(hydraulicLoop)

    occupiedNames = [l.name.value for l in hydraulicLoops.hydraulicLoops if l != hydraulicLoop]

    _common.setConnectionsSelected(hydraulicLoop.connections, True)

    okedOrCancelled = _gui.HydraulicLoopDialog.showDialog(guiHydraulicLoop, occupiedNames, fluids)

    _common.setConnectionsSelected(hydraulicLoop.connections, False)

    if okedOrCancelled == "cancelled":
        return

    _applyModel(guiHydraulicLoop, hydraulicLoop)


def _createGuiLoop(hydraulicLoop: _model.HydraulicLoop) -> _gmodel.HydraulicLoop:
    guiConnections = _createGuiConnections(hydraulicLoop)

    guiLoop = _gmodel.HydraulicLoop(
        hydraulicLoop.name.value, hydraulicLoop.fluid, hydraulicLoop.useLoopWideDefaults, guiConnections
    )
    return guiLoop


def _createGuiConnections(hydraulicLoop):
    if hydraulicLoop.useLoopWideDefaults:
        guiConnections = [
            _gmodel.Connection(
                c.displayName,
                _defaults.DEFAULT_DIAMETER_IN_CM,
                _defaults.DEFAULT_U_VALUE_IN_W_PER_M2_K,
                _defaults.DEFAULT_LENGTH_IN_M,
                _defaults.DEFAULT_SHALL_CREATE_TRNSYS_UNIT,
                c,
            )
            for c in hydraulicLoop.connections
        ]

        return guiConnections

    guiConnections = [
        _gmodel.Connection(c.displayName, c.diameterInCm, c.uValueInWPerM2K, c.lengthInM, c.shallBeSimulated, c)
        for c in hydraulicLoop.connections
    ]

    return guiConnections


def _applyModel(guiHydraulicLoop: _gmodel.HydraulicLoop, hydraulicLoop: _model.HydraulicLoop) -> None:
    oldName = hydraulicLoop.name.value
    newName = guiHydraulicLoop.name
    if oldName != newName:
        hydraulicLoop.name = _model.UserDefinedName(newName)

    hydraulicLoop.fluid = guiHydraulicLoop.fluid
    hydraulicLoop.useLoopWideDefaults = guiHydraulicLoop.useLoopWideDefaults

    if guiHydraulicLoop.useLoopWideDefaults:
        _lwd.resetConnectionPropertiesToLoopWideDefaults(hydraulicLoop.connections, hydraulicLoop.name.value)
    else:
        _applyConnectionModels(guiHydraulicLoop)


def _applyConnectionModels(guiHydraulicLoop: _gmodel.HydraulicLoop) -> None:
    for modelConnection in guiHydraulicLoop.connections:
        connection = modelConnection.connection

        connection.lengthInM = modelConnection.lengthInM
        connection.diameterInCm = modelConnection.diameterInCm
        connection.uValueInWPerM2K = modelConnection.uValueInWPerM2K
        connection.shallBeSimulated = modelConnection.shallBeSimulated
