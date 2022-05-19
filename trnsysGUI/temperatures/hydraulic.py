import typing as _tp

import trnsysGUI.internalPiping as _ip
import trnsysGUI.temperatures as _temps


def export(hasInternalPiping: _ip.HasInternalPiping) -> _tp.Sequence[str]:
    internalPiping = hasInternalPiping.getInternalPiping()

    equations = []
    for node in internalPiping.nodes:
        internalName = _temps.getInternalTemperatureVariableName(hasInternalPiping, node)
        name = _temps.getTemperatureVariableName(hasInternalPiping, node)
        equation = f"{name}={internalName}"
        equations.append(equation)

    return equations
