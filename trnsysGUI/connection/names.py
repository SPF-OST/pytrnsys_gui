import trnsysGUI.connection.connectionBase as _cb
import trnsysGUI.temperatures as _temps
from trnsysGUI import PortItemBase as _pib
from trnsysGUI.massFlowSolver import networkModel as _mfn, names as _mnames


def getTemperatureVariableName(connection: _cb.ConnectionBase, portItemType: _mfn.PortItemType) -> str:
    modelPipe = connection.getModelPipe(portItemType)
    variableName = _temps.getTemperatureVariableName(connection, modelPipe)
    return variableName


def getInputMassFlowVariableName(graphicalPortItem: _pib.PortItemBase, portItemType: _mfn.PortItemType) -> str:
    connection = graphicalPortItem.getConnection()
    connectionInternalPiping = connection.getInternalPiping()
    connectionNode = connectionInternalPiping.getNode(graphicalPortItem, portItemType)

    assert isinstance(connectionNode, _mfn.Pipe)

    connectionPortItem = connectionInternalPiping.getModelPortItem(graphicalPortItem, portItemType)

    oppositePortItem = (
        connectionNode.fromPort if connectionNode.toPort == connectionPortItem else connectionNode.toPort
    )

    variableName = _mnames.getMassFlowVariableName(connection, connectionNode, oppositePortItem)

    return variableName
