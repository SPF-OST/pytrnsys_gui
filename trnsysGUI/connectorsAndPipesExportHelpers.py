import typing as _tp

import jinja2 as _jinja

import trnsysGUI.massFlowSolver.names as _mnames
from trnsysGUI import internalPiping as _ip, PortItemBase as _pib, temperatures as _temps
from trnsysGUI.massFlowSolver import networkModel as _mfn


def getTemperatureVariableName(
    parent: _ip.HasInternalPiping, portItem: _pib.PortItemBase, portItemType: _mfn.PortItemType
) -> str:
    parentInternalPiping = parent.getInternalPiping()
    node = parentInternalPiping.getNode(portItem, portItemType)
    temperatureVariableName = _temps.getTemperatureVariableName(
        parent.shallRenameOutputTemperaturesInHydraulicFile(),
        componentDisplayName=parent.getDisplayName(),
        nodeName=node.name,
    )
    return temperatureVariableName


_IF_THEN_ELSE_UNIT_TEMPLATE = _jinja.Template(
    """\
{%- if componentName %}
! {{componentName}}
{% endif -%}
UNIT {{unitNumber}} TYPE 222
INPUTS 3
{{massFlowRate}} {{posFlowInputTemp}} {{negFlowInputTemp}}
***
0 20 20
EQUATIONS {{2 if canonicalMassFlowRate else 1}}
{{outputTemp}} = [{{unitNumber}},1]
{%- if canonicalMassFlowRate %}
{{canonicalMassFlowRate}} = {{massFlowRate}}
{%- endif -%}
""",
    trim_blocks=False,
    keep_trailing_newline=False,
)


def getIfThenElseUnit(  # pylint: disable=too-many-arguments
    unitNumber: int,
    outputTemp: str,
    massFlowRate: str,
    posFlowInputTemp: str,
    negFlowInputTemp: str,
    canonicalMassFlowRate: _tp.Optional[str] = None,
    componentName: _tp.Optional[str] = None,
    extraNewlines: str = "\n\n",
) -> str:
    unitText = _IF_THEN_ELSE_UNIT_TEMPLATE.render(
        unitNumber=unitNumber,
        outputTemp=outputTemp,
        massFlowRate=massFlowRate,
        posFlowInputTemp=posFlowInputTemp,
        negFlowInputTemp=negFlowInputTemp,
        componentName=componentName,
        canonicalMassFlowRate=canonicalMassFlowRate,
    )

    unitText += extraNewlines

    return unitText


def getInputMfrName(hasInternalPiping: _ip.HasInternalPiping, pipe: _mfn.Pipe) -> str:
    return _mnames.getMassFlowVariableName(hasInternalPiping, pipe, pipe.fromPort)
