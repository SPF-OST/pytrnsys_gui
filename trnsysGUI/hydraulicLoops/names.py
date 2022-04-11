def getHeatCapacityName(loopName: str) -> str:
    return f"L{loopName}Cp"


def getDensityName(loopName: str) -> str:
    return f"L{loopName}Rho"


def getDefaultDiameterName(loopName: str) -> str:
    return f"{loopName}Dia"


def getDefaultUValueName(loopName: str) -> str:
    return f"{loopName}UVal"


def getDefaultLengthName(loopName: str) -> str:
    return f"{loopName}Len"


def getNumberOfPipesName(loopName: str) -> str:
    return f"{loopName}NPipes"
