import typing as _tp


def getInternalTemperatureVariableName(
    *, componentDisplayName: str, nodeName: _tp.Optional[str] = None
) -> str:
    nodeNameOrEmpty = nodeName or ""
    temperatureVariableName = f"T{componentDisplayName}{nodeNameOrEmpty}"
    return temperatureVariableName


def getTemperatureVariableName(
    shallRenameOutputInHydraulicFile: bool,
    *,
    componentDisplayName: str,
    nodeName: _tp.Optional[str],
) -> str:
    internalName = getInternalTemperatureVariableName(
        componentDisplayName=componentDisplayName, nodeName=nodeName
    )

    if not shallRenameOutputInHydraulicFile:
        return internalName

    return f"{internalName}H"
