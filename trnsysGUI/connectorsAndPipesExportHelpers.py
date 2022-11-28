import trnsysGUI.massFlowSolver.names as _mnames
from trnsysGUI import internalPiping as _ip, PortItemBase as _pib, temperatures as _temps
from trnsysGUI.massFlowSolver import networkModel as _mfn


def getTemperatureVariableName(
    parent: _ip.HasInternalPiping, portItem: _pib.PortItemBase, portItemType: _mfn.PortItemType
) -> str:
    parentInternalPiping = parent.getInternalPiping()
    node = parentInternalPiping.getNode(portItem, portItemType)
    temperatureVariableName = _temps.getTemperatureVariableName(parent, node)
    return temperatureVariableName


def getIfThenElseEquation(outputTemp: str, massFlowRate: str, posFlowInputTemp: str, negFlowInputTemp: str) -> str:
    equation = f"{outputTemp} = GE({massFlowRate}, 0)*{posFlowInputTemp} + LE({massFlowRate}, 0)*{negFlowInputTemp}"
    return equation


def getIfThenElseUnit(
    unitNumber: int, outputTemp: str, massFlowRate: str, posFlowInputTemp: str, negFlowInputTemp: str
) -> str:
    unitText = f"""\
UNIT {unitNumber} TYPE 222
INPUTS 3
{massFlowRate} {posFlowInputTemp} {negFlowInputTemp}
***
0 20 20

EQUATIONS 1
{outputTemp} = [{unitNumber},1]

"""
    return unitText


def getInputMfrName(hasInternalPiping: _ip.HasInternalPiping, pipe: _mfn.Pipe) -> str:
    return _mnames.getMassFlowVariableName(hasInternalPiping, pipe, pipe.fromPort)
