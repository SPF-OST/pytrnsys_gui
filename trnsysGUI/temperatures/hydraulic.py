import typing as _tp

import trnsysGUI.internalPiping as _ip
import trnsysGUI.temperatures as _temps


def export(hasInternalPiping: _ip.HasInternalPiping) -> _tp.Sequence[str]:
    internalPiping = hasInternalPiping.getInternalPiping()

    equations = []
    for node in internalPiping.nodes:
        internalName = _temps.getInternalTemperatureVariableName(
            componentDisplayName=hasInternalPiping.getDisplayName(), nodeName=node.name
        )
        name = _temps.getTemperatureVariableName(
            hasInternalPiping.shallRenameOutputTemperaturesInHydraulicFile(),
            componentDisplayName=hasInternalPiping.getDisplayName(),
            nodeName=node.name,
        )
        equation = f"{name}={internalName}"
        equations.append(equation)

    return equations
