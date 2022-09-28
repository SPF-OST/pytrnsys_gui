import trnsysGUI.internalPiping as _ip
import trnsysGUI.massFlowSolver.networkModel as _mfn


def getInternalTemperatureVariableName(hasInternalPiping: _ip.HasInternalPiping, node: _mfn.Node) -> str:
    nodeNameOrEmpty = node.name or ""
    temperatureVariableName = f"T{hasInternalPiping.getDisplayName()}{nodeNameOrEmpty}"
    return temperatureVariableName


def getTemperatureVariableName(hasInternalPiping: _ip.HasInternalPiping, node: _mfn.Node) -> str:
    internalName = getInternalTemperatureVariableName(hasInternalPiping, node)

    if not hasInternalPiping.shallRenameOutputTemperaturesInHydraulicFile():
        return internalName

    return f"{internalName}H"
