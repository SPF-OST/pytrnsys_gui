import trnsysGUI.ddckFields.headerAndParameters.getDoublePipeConnectionHeaderAndParameters as _dpc


def getHeaderAndParametersGenerator(version: str):
    options = {"DoublePipeConnection": _dpc.getDoublePipeConnectionHeaderAndParameters}

    if version in options:
        return options[version]
    raise ValueError(f"getHeaderAndParameters Received unsupported blockItem: {version}")
