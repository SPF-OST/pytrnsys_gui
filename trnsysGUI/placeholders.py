import pathlib as _pl
import typing as _tp

import pytrnsys.utils.result as _res

import trnsysGUI.BlockItem as _bi
import trnsysGUI.PortItemBase as _pib
import trnsysGUI.internalPiping as _ip
import trnsysGUI.massFlowSolver.names as _mnames
import trnsysGUI.massFlowSolver.networkModel as _mfn
import trnsysGUI.temperatures as _temps


def getPlaceholderValues(ddckDirNames: _tp.Sequence[str], trnsysObjects) -> _res.Result[dict]:
    allPlaceholders = {}
    for component in trnsysObjects:
        if not (
            isinstance(component, _ip.HasInternalPiping)
            and isinstance(component, _bi.BlockItem)
            and component.hasDdckPlaceHolders()
        ):
            continue

        if not component.path:
            return _res.Error(f"{component.displayName} doesn't have ddck template path.")

        componentPath = _pl.Path(component.path)
        componentName = componentPath.stem
        if componentName not in ddckDirNames:
            return _res.Error(f"No directory called `{componentName}` found in the project folder.")

        placeholders = {}
        internalPiping = component.getInternalPiping()
        for node in internalPiping.nodes:
            for modelPortItem in node.getPortItems():
                if modelPortItem.direction == _mfn.PortItemDirection.OUTPUT:
                    placeholders[modelPortItem.name] = {
                        "@temp": _temps.getInternalTemperatureVariableName(component, node)
                    }
                elif modelPortItem.direction == _mfn.PortItemDirection.INPUT:
                    graphicalPortItem = internalPiping.modelPortItemsToGraphicalPortItem[modelPortItem]

                    inputTemperatureVariableName = _getInputTemperatureVariableName(modelPortItem, graphicalPortItem)
                    inputMfrVariableName = _getInputMassFlowVariableName(modelPortItem, graphicalPortItem)

                    placeholders[modelPortItem.name] = {
                        "@temp": inputTemperatureVariableName,
                        "@mfr": inputMfrVariableName
                    }

        allPlaceholders[componentName] = placeholders

    return allPlaceholders


def _getInputTemperatureVariableName(modelPortItem: _mfn.PortItem, graphicalPortItem: _pib.PortItemBase) -> str:
    connection = graphicalPortItem.getConnection()
    connectionInternalPiping = connection.getInternalPiping()
    connectionNode = connectionInternalPiping.getNode(graphicalPortItem, modelPortItem.type)
    variableName = _temps.getTemperatureVariableName(connection, connectionNode)
    return variableName


def _getInputMassFlowVariableName(modelPortItem: _mfn.PortItem, graphicalPortItem: _pib.PortItemBase) -> str:
    connection = graphicalPortItem.getConnection()
    connectionInternalPiping = connection.getInternalPiping()
    connectionNode = connectionInternalPiping.getNode(graphicalPortItem, modelPortItem.type)

    assert isinstance(connectionNode, _mfn.Pipe)

    connectionPortItem = connectionInternalPiping.getModelPortItem(graphicalPortItem, modelPortItem.type)

    oppositePortItem = (
        connectionNode.fromPort if connectionNode.toPort == connectionPortItem else connectionNode.toPort
    )

    variableName = _mnames.getMassFlowVariableName(connection, connectionNode, oppositePortItem)

    return variableName
