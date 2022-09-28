import trnsysGUI.PortItemBase as _pib
import trnsysGUI.internalPiping as _ip
from trnsysGUI import temperatures as _temps
from trnsysGUI.massFlowSolver import networkModel as _mfn


def getTemperatureVariableName(
    parent: _ip.HasInternalPiping, portItem: _pib.PortItemBase, portItemType: _mfn.PortItemType
) -> str:
    parentInternalPiping = parent.getInternalPiping()
    node = parentInternalPiping.getNode(portItem, portItemType)
    temperatureVariableName = _temps.getTemperatureVariableName(parent, node)
    return temperatureVariableName
