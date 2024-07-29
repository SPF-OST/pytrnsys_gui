import collections.abc as _cabc
import typing as _tp

import pytrnsys.utils.result as _res

import trnsysGUI.internalPiping as _ip
import trnsysGUI.massFlowSolver.networkModel as _mfn

from . import models as _models


def createModelConnectionsFromInternalPiping(
    internalPiping: _ip.InternalPiping,
) -> _res.Result[_cabc.Set[_models.Connection]]:
    connections = set()
    for node in internalPiping.nodes:
        if not isinstance(node, _mfn.Pipe):
            return _res.Error(f"`{node.name}` is a `{node.__class__.__name__}`, but only direct pipes are supported.")
        pipe = node

        inputPort = _models.InputPort(pipe.fromPort.name)
        outputPort = _models.OutputPort(pipe.toPort.name)

        connection = _models.Connection(pipe.name, inputPort, outputPort)

        connections.add(connection)

    return connections


_StringMapping = _tp.Mapping[str, _tp.Any]


def createModelConnectionsFromProforma(
    serializedConnections: _cabc.Sequence[_StringMapping], variables: _cabc.Sequence[_models.Variable]
) -> _res.Result[_cabc.Sequence[_models.Connection]]:
    variablesByOrder = {v.order: v for v in variables}

    connections = [_createConnection(s, variablesByOrder) for s in serializedConnections]

    return connections


def _createConnection(
    serializedConnection: _StringMapping, variablesByOrder: _cabc.Mapping[int, _models.Variable]
) -> _models.Connection:
    serializedInputPort = serializedConnection["input"]
    inputPort = _createInputPort(serializedInputPort, variablesByOrder)

    outputPort = _createOutputPort(serializedConnection, variablesByOrder)

    name = serializedConnection.get("@name")

    fluidDensityVariable = _getOptionalVariable(serializedInputPort, "fluidDensity", variablesByOrder)
    fluidHeatCapacityVariable = _getOptionalVariable(serializedInputPort, "fluidHeatCapacity", variablesByOrder)
    fluid = _models.Fluid(fluidDensityVariable, fluidHeatCapacityVariable)

    connection = _models.Connection(name, inputPort, outputPort, fluid)

    return connection


def _createInputPort(
    serializedInputPort: _StringMapping, variablesByOrder: _cabc.Mapping[int, _models.Variable]
) -> _models.InputPort:
    name = serializedInputPort["@name"]
    massFlowRateVariable = _getVariable(serializedInputPort, "massFlowRate", variablesByOrder)
    temperatureVariable = _getVariable(serializedInputPort, "temperature", variablesByOrder)
    inputPort = _models.InputPort(name, temperatureVariable, massFlowRateVariable)
    return inputPort


def _createOutputPort(
    serializedConnection: _StringMapping, variablesByOrder: _cabc.Mapping[int, _models.Variable]
) -> _models.OutputPort:
    serializedOutputPort = serializedConnection["output"]
    name = serializedOutputPort["@name"]
    temperature = _getVariable(serializedOutputPort, "temperature", variablesByOrder)
    reverseTemperature = _getOptionalVariable(serializedOutputPort, "reverseTemperature", variablesByOrder)
    outputPort = _models.OutputPort(name, temperature, reverseTemperature)
    return outputPort


def _getVariable(
    serializedPort: _StringMapping, variableName: str, variablesByOrder: _cabc.Mapping[int, _models.Variable]
) -> _models.Variable:
    variable = _getOptionalVariable(serializedPort, variableName, variablesByOrder)
    portName = serializedPort["@name"]
    assert variable, f"No associated `{variableName}` variable for port {portName}"
    return variable


def _getOptionalVariable(
    serializedPort: _StringMapping, variableName: str, variablesByOrder: _cabc.Mapping[int, _models.Variable]
) -> _tp.Optional[_models.Variable]:
    child = serializedPort.get(variableName)
    if not child:
        return None

    order = child["variableReference"]["order"]
    variable = variablesByOrder[order]
    return variable
