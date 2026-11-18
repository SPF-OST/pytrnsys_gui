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


def getNominalPowerName(loopName: str) -> str:
    return f"{loopName}PNom"


def getNominalTemperatureDifferenceName(loopName: str) -> str:
    return f"{loopName}dTNom"


def getNominalVolumeFlowRateName(loopName: str) -> str:
    return f"{loopName}VfrNom"


def getNominalMassFlowRateName(loopName: str) -> str:
    return f"{loopName}MfrNom"


def getNominalDiameterName(loopName: str) -> str:
    return f"{loopName}DN"


def getInsulationThermalConductivityName(loopName: str) -> str:
    return f"{loopName}LamIns"


def getInsulationThicknessName(loopName: str) -> str:
    return f"{loopName}sIns"


def getLinearHeatLossCoefficientName(loopName: str) -> str:
    return f"{loopName}ULin"
