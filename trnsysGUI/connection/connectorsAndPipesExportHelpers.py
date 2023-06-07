import typing as _tp

import jinja2 as _jinja

import trnsysGUI.PortItemBase as _pib
import trnsysGUI.globalNames as _gnames
import trnsysGUI.internalPiping as _ip
import trnsysGUI.massFlowSolver.names as _mnames
import trnsysGUI.massFlowSolver.networkModel as _mfn
import trnsysGUI.temperatures as _temps


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
    f"""\
<%- if componentName %>
! <<componentName>>
<% endif -%>
UNIT <<unitNumber>> TYPE <<typeNumber>>
<% if typeNumber == 223 %>
PARAMETERS 4
{_gnames.MassFlowSolver.ABSOLUTE_TOLERANCE}
{_gnames.MassFlowSolver.RELATIVE_TOLERANCE}
{_gnames.MassFlowSolver.SWITCHING_THRESHOLD}
<<initialTemp>>
<% endif -%>
INPUTS 3
<<massFlowRate>> <<posFlowInputTemp>> <<negFlowInputTemp>>
***
0 <<initialTemp>> <<initialTemp>>
EQUATIONS <<2 if canonicalMassFlowRate else 1>>
<<outputTemp>> = [<<unitNumber>>,1]
<%- if canonicalMassFlowRate %>
<<canonicalMassFlowRate>> = <<massFlowRate>>
<%- endif -%>
""",
    block_start_string="<%",
    block_end_string="%>",
    variable_start_string="<<",
    variable_end_string=">>",
    trim_blocks=False,
    keep_trailing_newline=False,
)


def getIfThenElseUnit(
    unitNumber: int,
    outputTemp: str,
    initialTemp: str,
    massFlowRate: str,
    posFlowInputTemp: str,
    negFlowInputTemp: str,
    *,
    typeNumber: _tp.Literal[222, 223] = 222,
    canonicalMassFlowRate: _tp.Optional[str] = None,
    componentName: _tp.Optional[str] = None,
    extraNewlines: str = "\n\n",
) -> str:
    unitText = _IF_THEN_ELSE_UNIT_TEMPLATE.render(
        unitNumber=unitNumber,
        typeNumber=typeNumber,
        outputTemp=outputTemp,
        initialTemp=initialTemp,
        massFlowRate=massFlowRate,
        posFlowInputTemp=posFlowInputTemp,
        negFlowInputTemp=negFlowInputTemp,
        componentName=componentName,
        canonicalMassFlowRate=canonicalMassFlowRate,
    )

    unitText += extraNewlines

    return unitText


def getInputMfrName(displayName: str, pipe: _mfn.Pipe) -> str:
    return _mnames.getMassFlowVariableName(displayName, pipe, pipe.fromPort)
