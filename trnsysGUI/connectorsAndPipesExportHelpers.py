import trnsysGUI.massFlowSolver.networkModel as _mfn


def getEquation(outputTemp: str, massFlowRate: str, posFlowInputTemp: str, negFlowInputTemp: str) -> str:
    coldEquation = f"{outputTemp} = GE({massFlowRate}, 0)*{posFlowInputTemp} + LE({massFlowRate}, 0)*{negFlowInputTemp}"
    return coldEquation


def getMfrName(pipe: _mfn.Pipe) -> str:
    outputVariable = pipe.getOutputVariables()[0]
    assert outputVariable
    mfrName = outputVariable.name
    return mfrName
