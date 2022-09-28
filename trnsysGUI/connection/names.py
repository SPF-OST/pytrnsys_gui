import trnsysGUI.connection.connectionBase as _cb
import trnsysGUI.temperatures as _temps
import trnsysGUI.massFlowSolver.networkModel as _mfn


def getTemperatureVariableName(connection: _cb.ConnectionBase, portItemType: _mfn.PortItemType) -> str:
    modelPipe = connection.getModelPipe(portItemType)
    variableName = _temps.getTemperatureVariableName(connection, modelPipe)
    return variableName


def getHeatLossVariableName(connection: _cb.ConnectionBase, portItemType: _mfn.PortItemType) -> str:
    modelPipe = connection.getModelPipe(portItemType)
    variableName = f"P{connection.getDisplayName()}{modelPipe.name or ''}_kW"
    return variableName
