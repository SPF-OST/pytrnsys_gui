import trnsysGUI.PortItemBase as _pib
import trnsysGUI.connection.connectionBase as _cb
import trnsysGUI.massFlowSolver.networkModel as _mfn
import trnsysGUI.names.create as _nc
import trnsysGUI.temperatures as _temps


def getTemperatureVariableName(
    connection: _cb.ConnectionBase, portItemType: _mfn.PortItemType
) -> str:
    modelPipe = connection.getModelPipe(portItemType)
    variableName = _temps.getTemperatureVariableName(
        connection.shallRenameOutputTemperaturesInHydraulicFile(),
        componentDisplayName=connection.displayName,
        nodeName=modelPipe.name,
    )
    return variableName


def generateDefaultConnectionName(
    fromPort: _pib.PortItemBase,
    toPort: _pib.PortItemBase,
    createNamingHelper: _nc.CreateNamingHelper,
) -> str:
    baseName = getDefaultConnectionNameBase(fromPort, toPort)
    defaultDisplayName = createNamingHelper.generateName(
        baseName, checkDdckFolder=False, firstGeneratedNameHasNumber=False
    )
    return defaultDisplayName


def getDefaultConnectionNameBase(
    fromPort: _pib.PortItemBase, toPort: _pib.PortItemBase
) -> str:
    fromDisplayName = fromPort.parent.getDisplayName()
    toDisplayName = toPort.parent.getDisplayName()
    return f"{fromDisplayName}_{toDisplayName}"


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
