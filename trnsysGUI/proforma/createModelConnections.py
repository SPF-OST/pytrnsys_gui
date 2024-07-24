import collections.abc as _cabc
import typing as _tp

import pytrnsys.utils.result as _res

import trnsysGUI.internalPiping as _ip
import trnsysGUI.massFlowSolver.networkModel as _mfn

from . import modelConnection as _mc


def createModelConnectionsFromInternalPiping(
    internalPiping: _ip.InternalPiping,
) -> _res.Result[_cabc.Set[_mc.Connection]]:
    connections = set()
    for node in internalPiping.nodes:
        if not isinstance(node, _mfn.Pipe):
            return _res.Error(f"`{node.name}` is a `{node.__name__}`, but only direct pipes are supported.")
        pipe = node

        inputPort = _mc.InputPort(pipe.fromPort.name)
        outputPort = _mc.OutputPort(pipe.toPort.name)

        connection = _mc.Connection(pipe.name, inputPort, outputPort)

        connections.add(connection)

    return connections


_StringMapping = _tp.Mapping[str, _tp.Any]
_SerializedVariable = _StringMapping


def _createVariable(serializedVariable: _SerializedVariable) -> _mc.Variable:
    variable = _mc.Variable(
        serializedVariable["name"], serializedVariable.get("definition"), serializedVariable["order"]
    )

    return variable


def _createVariablesByOrder(serializedVariables: _cabc.Set[_SerializedVariable]) -> _cabc.Mapping[int, _mc.Variable]:
    variables = [_createVariable(s) for s in serializedVariables]
    variablesByOrder = {v.order: v for v in variables}
    return variablesByOrder


def createModelConnectionsFromProforma(
    serializedConnections: _cabc.Sequence[_StringMapping], serializedVariables: _cabc.Set[_StringMapping]
) -> _res.Result[_cabc.Set[_mc.Connection]]:
    variablesByOrder = _createVariablesByOrder(serializedVariables)

    connections = {_createConnection(s, variablesByOrder) for s in serializedConnections}

    return connections


def _createConnection(
    serializedConnection: _StringMapping, variablesByOrder: _cabc.Mapping[int, _mc.Variable]
) -> _mc.Connection:
    serializedInputPort = serializedConnection["input"]
    inputPort = _createInputPort(serializedInputPort, variablesByOrder)

    outputPort = _createOutputPort(serializedConnection, variablesByOrder)

    name = serializedConnection.get("@name")

    fluidDensityVariable = _getOptionalVariable(serializedInputPort, "fluidDensity", variablesByOrder)
    fluidHeatCapacityVariable = _getOptionalVariable(serializedInputPort, "fluidHeatCapacity", variablesByOrder)
    fluid = _mc.Fluid(fluidDensityVariable, fluidHeatCapacityVariable)

    connection = _mc.Connection(name, inputPort, outputPort, fluid)

    return connection


def _createInputPort(
    serializedInputPort: _StringMapping, variablesByOrder: _cabc.Mapping[int, _mc.Variable]
) -> _mc.InputPort:
    name = serializedInputPort["@name"]
    massFlowRateVariable = _getVariable(serializedInputPort, "massFlowRate", variablesByOrder)
    temperatureVariable = _getVariable(serializedInputPort, "temperature", variablesByOrder)
    inputPort = _mc.InputPort(name, temperatureVariable, massFlowRateVariable)
    return inputPort


def _createOutputPort(
    serializedConnection: _StringMapping, variablesByOrder: _cabc.Mapping[int, _mc.Variable]
) -> _mc.OutputPort:
    serializedOutputPort = serializedConnection["output"]
    name = serializedOutputPort["@name"]
    temperature = _getVariable(serializedOutputPort, "temperature", variablesByOrder)
    reverseTemperature = _getOptionalVariable(serializedOutputPort, "reverseTemperature", variablesByOrder)
    outputPort = _mc.OutputPort(name, temperature, reverseTemperature)
    return outputPort


def _getVariable(
    serializedPort: _StringMapping, variableName: str, variablesByOrder: _cabc.Mapping[int, _mc.Variable]
) -> _mc.Variable:
    variable = _getOptionalVariable(serializedPort, variableName, variablesByOrder)
    portName = serializedPort["@name"]
    assert variable, f"No associated `{variableName}` variable for port {portName}"
    return variable


def _getOptionalVariable(
    serializedPort: _StringMapping, variableName: str, variablesByOrder: _cabc.Mapping[int, _mc.Variable]
) -> _tp.Optional[_mc.Variable]:
    child = serializedPort.get(variableName)
    if not child:
        return None

    order = child["variableReference"]["order"]
    variable = variablesByOrder[order]
    return variable
