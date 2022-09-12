import trnsysGUI.internalPiping as _ip
import trnsysGUI.massFlowSolver.names as _mnames
import trnsysGUI.massFlowSolver.networkModel as _mfn


def getEquation(outputTemp: str, massFlowRate: str, posFlowInputTemp: str, negFlowInputTemp: str) -> str:
    equation = f"{outputTemp} = GE({massFlowRate}, 0)*{posFlowInputTemp} + LE({massFlowRate}, 0)*{negFlowInputTemp}"
    return equation


def getInputMfrName(hasInternalPiping: _ip.HasInternalPiping, pipe: _mfn.Pipe) -> str:
    return _mnames.getMassFlowVariableName(hasInternalPiping, pipe, pipe.fromPort)
