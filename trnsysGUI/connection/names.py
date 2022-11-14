import trnsysGUI.connection.connectionBase as _cb
import trnsysGUI.massFlowSolver.networkModel as _mfn
import trnsysGUI.temperatures as _temps


def getTemperatureVariableName(connection: _cb.ConnectionBase, portItemType: _mfn.PortItemType) -> str:
    modelPipe = connection.getModelPipe(portItemType)
    variableName = _temps.getTemperatureVariableName(connection, modelPipe)
    return variableName


class EnergyBalanceTotals:
    class SinglePipe:
        PIPE_INTERNAL_CHANGE = "spPipeIntTot"
        DISSIPATED = "PipeLossTot"
        CONVECTED = "spPipeConvectedTot"
        IMBALANCE = "spImbalance"

    class DoublePipe:
        PIPE_INTERNAL_CHANGE = "dpPipeIntTot"
        SOIL_INTERNAL_CHANGE = "dpSoilIntTot"
        CONVECTED = "dpPipeConvectedTot"
        DISSIPATION_TO_FAR_FIELD = "dpToFFieldTot"
        IMBALANCE = "dpImbalance"
