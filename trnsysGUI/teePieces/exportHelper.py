import dataclasses as _dc
import typing as _tp

import jinja2 as _jinja

from trnsysGUI import temperatures as _temps
from trnsysGUI.connection import names as _cnames
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
    initialValue: _tp.Union[str, float]


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
    node: _mfn.TeePiece,
    portItemType: _mfn.PortItemType,
    initialTemperature: _tp.Union[str, float],
    componentName: _tp.Optional[str] = None,
    extraNewlines: str = "",
):
    inputPort, orthogonalOutputPort, straightOutputPort = _createPorts(teePiece, node, portItemType, initialTemperature)

    outputTemperature = _temps.getInternalTemperatureVariableName(
        componentDisplayName=teePiece.displayName, nodeName=node.name
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


def _createPorts(teePiece, node, portItemType, initialTemperature):
    inputMassFlow = _mnames.getMassFlowVariableName(teePiece, node, node.input)
    inputTemperature = _cnames.getTemperatureVariableName(teePiece.inputs[0].getConnection(), portItemType)
    inputPort = _Port(_Variable(inputMassFlow, 0), _Variable(inputTemperature, initialTemperature))
    straightOutMassFlow = _mnames.getMassFlowVariableName(teePiece, node, node.output1)
    straightOutputTemperature = _cnames.getTemperatureVariableName(teePiece.outputs[0].getConnection(), portItemType)
    straightOutputPort = _Port(
        _Variable(straightOutMassFlow, 0), _Variable(straightOutputTemperature, initialTemperature)
    )
    orthogonalOutMassFlow = _mnames.getMassFlowVariableName(teePiece, node, node.output2)
    orthogonalOutputTemperature = _cnames.getTemperatureVariableName(teePiece.outputs[1].getConnection(), portItemType)
    orthogonalOutputPort = _Port(
        _Variable(orthogonalOutMassFlow, 0), _Variable(orthogonalOutputTemperature, initialTemperature)
    )
    return inputPort, orthogonalOutputPort, straightOutputPort
