from . import model as _model


def getHeatCapacityName(loop: _model.HydraulicLoop) -> str:
    return f"L{loop.name.value}Cp"


def getDensityName(loop: _model.HydraulicLoop) -> str:
    return f"L{loop.name.value}Rho"
