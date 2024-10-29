import dataclasses as _dc
import typing as _tp

import jinja2 as _jinja

import trnsysGUI.temperatures as _temps
import trnsysGUI.connection.names as _cnames
import trnsysGUI.connection.connectionBase as _cb
from trnsysGUI.massFlowSolver import networkModel as _mfn, names as _mnames
from trnsysGUI.teePieces import teePieceBase as _tpb


_TEE_PIECE_UNIT_TEMPLATE = _jinja.Template(
    """\
! {{componentName}}
UNIT {{unitNumber}} TYPE 929
{%- if componentName %}
{% endif -%}
INPUTS 6
{{inputPort.massFlow.name}}
{{straightOutputPort.massFlow.name}}
{{orthogonalOutputPort.massFlow.name}}
{{inputPort.temperature.name}}
{{straightOutputPort.temperature.name}}
{{orthogonalOutputPort.temperature.name}}
***
{{inputPort.massFlow.initialValue}}
{{straightOutputPort.massFlow.initialValue}}
{{orthogonalOutputPort.massFlow.initialValue}}
{{inputPort.temperature.initialValue}}
{{straightOutputPort.temperature.initialValue}}
{{orthogonalOutputPort.temperature.initialValue}}
EQUATIONS 1
{{resultingOutputTemperature}} = [{{unitNumber}},1]
""",
    trim_blocks=False,
    keep_trailing_newline=False,
)


@_dc.dataclass
class _Variable:
    name: str
    initialValue: str | float


@_dc.dataclass
class _Port:
    massFlow: _Variable
    temperature: _Variable


def _renderTeePieceUnit(
    unitNumber: int,
    inputPort: _Port,
    straightOutputPort: _Port,
    orthogonalOutputPort: _Port,
    resultingOutputTemperature: str,
    *,
    componentName: _tp.Optional[str],
    extraNewlines: str,
) -> str:
    unitText = _TEE_PIECE_UNIT_TEMPLATE.render(
        unitNumber=unitNumber,
        inputPort=inputPort,
        straightOutputPort=straightOutputPort,
        orthogonalOutputPort=orthogonalOutputPort,
        resultingOutputTemperature=resultingOutputTemperature,
        componentName=componentName,
    )

    unitText += extraNewlines

    return unitText


def getTeePieceUnit(
    unitNumber: int,
    teePiece: _tpb.TeePieceBase,
    massFlowNetworkNode: _mfn.TeePiece,
    portItemType: _mfn.PortItemType,
    initialTemperature: str | float,
    componentName: _tp.Optional[str] = None,
    extraNewlines: str = "",
) -> str:

    inputPort, orthogonalOutputPort, straightOutputPort = _createPorts(
        teePiece, massFlowNetworkNode, portItemType, initialTemperature
    )

    outputTemperature = _temps.getInternalTemperatureVariableName(
        componentDisplayName=teePiece.displayName,
        nodeName=massFlowNetworkNode.name,
    )

    unitText = _renderTeePieceUnit(
        unitNumber,
        inputPort,
        straightOutputPort,
        orthogonalOutputPort,
        outputTemperature,
        componentName=componentName,
        extraNewlines=extraNewlines,
    )

    return unitText


def _createPorts(
    teePiece: _tpb.TeePieceBase,
    massFlowNetworkNode: _mfn.TeePiece,
    portItemType: _mfn.PortItemType,
    initialTemperature: str | float,
) -> _tp.Tuple[_Port, _Port, _Port]:

    inputPort = _createPort(
        teePiece.inputs[0].getConnection(),
        massFlowNetworkNode.input,
        teePiece,
        massFlowNetworkNode,
        portItemType,
        initialTemperature,
    )

    straightOutputPort = _createPort(
        teePiece.outputs[0].getConnection(),
        massFlowNetworkNode.output1,
        teePiece,
        massFlowNetworkNode,
        portItemType,
        initialTemperature,
    )

    orthogonalOutputPort = _createPort(
        teePiece.outputs[1].getConnection(),
        massFlowNetworkNode.output2,
        teePiece,
        massFlowNetworkNode,
        portItemType,
        initialTemperature,
    )

    return inputPort, orthogonalOutputPort, straightOutputPort


def _createPort(
    connection: _cb.ConnectionBase,
    modelPortItem: _mfn.PortItem,
    teePiece: _tpb.TeePieceBase,
    massFlowNetworkNode: _mfn.TeePiece,
    portItemType: _mfn.PortItemType,
    initialTemperature: str | float,
) -> _Port:

    massFlowName = _mnames.getMassFlowVariableName(
        teePiece.displayName, massFlowNetworkNode, modelPortItem
    )
    temperatureName = _cnames.getTemperatureVariableName(
        connection, portItemType
    )
    port = _Port(
        _Variable(massFlowName, 0),
        _Variable(temperatureName, initialTemperature),
    )
    return port
