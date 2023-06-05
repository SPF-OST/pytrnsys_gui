import pathlib as _pl
import typing as _tp

import pytrnsys.utils.result as _res
import trnsysGUI.BlockItem as _bi
import trnsysGUI.connection.connectionBase as _cb
import trnsysGUI.connection.names as _cnames
import trnsysGUI.connection.singlePipeConnection as _spc
import trnsysGUI.hydraulicLoops.model as _hlm
import trnsysGUI.hydraulicLoops.names as _lnames
import trnsysGUI.internalPiping as _ip
import trnsysGUI.massFlowSolver.names as _mnames
import trnsysGUI.massFlowSolver.networkModel as _mfn
import trnsysGUI.temperatures as _temps


def getPlaceholderValues(
    ddckDirNames: _tp.Sequence[str], trnsysObjects, hydraulicLoops: _hlm.HydraulicLoops
) -> _res.Result[dict]:
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

        placholdersForComponent = {}
        internalPiping = component.getInternalPiping()
        for node in internalPiping.nodes:
            for modelPortItem in node.getPortItems():
                nodeNameOrEmpty = node.name or ""
                qualifiedPortName = f"{nodeNameOrEmpty}{modelPortItem.name}"

                placeholdersForPort = _getPlaceholdersForPort(
                    hydraulicLoops, component, internalPiping, node, modelPortItem
                )

                placholdersForComponent[qualifiedPortName] = placeholdersForPort

        allPlaceholders[componentName] = placholdersForComponent

    return allPlaceholders


def _getPlaceholdersForPort(
    hydraulicLoops: _hlm.HydraulicLoops,
    component: _ip.HasInternalPiping,
    internalPiping: _ip.InternalPiping,
    node: _mfn.Node,
    modelPortItem: _mfn.PortItem,
) -> _tp.Dict[str, str]:
    displayName = component.getDisplayName()

    if modelPortItem.direction == _mfn.PortItemDirection.OUTPUT:
        outputTemperatureVariableName = _temps.getInternalTemperatureVariableName(
            componentDisplayName=displayName, nodeName=node.name
        )
        reverseInputTemperatureVariableName = _getTemperatureOfPipeConnectedAt(internalPiping, modelPortItem)

        placeholdersForPort = _createOutputPlaceholdersDict(
            outputTemperatureVariableName, reverseInputTemperatureVariableName
        )

        return placeholdersForPort

    if modelPortItem.direction == _mfn.PortItemDirection.INPUT:
        inputTemperatureVariableName = _getTemperatureOfPipeConnectedAt(internalPiping, modelPortItem)
        inputMfrVariableName = _mnames.getMassFlowVariableName(displayName, node, modelPortItem)

        inputConnection = _getConnectionAt(internalPiping, modelPortItem)
        loop = _getLoop(hydraulicLoops, inputConnection)

        placeholdersForPort = _createInputPlaceholdersDict(inputMfrVariableName, inputTemperatureVariableName, loop)

        return placeholdersForPort

    raise AssertionError(f"Unknown {_mfn.PortItemDirection.__name__}: {modelPortItem.direction}")


def _getTemperatureOfPipeConnectedAt(internalPiping: _ip.InternalPiping, modelPortItem: _mfn.PortItem) -> str:
    inputConnection = _getConnectionAt(internalPiping, modelPortItem)
    inputTemperatureVariableName = _cnames.getTemperatureVariableName(inputConnection, modelPortItem.type)
    return inputTemperatureVariableName


def _getConnectionAt(internalPiping: _ip.InternalPiping, modelPortItem: _mfn.PortItem) -> _cb.ConnectionBase:
    graphicalPortItem = internalPiping.modelPortItemsToGraphicalPortItem[modelPortItem]
    connection = graphicalPortItem.getConnection()
    return connection


def _createInputPlaceholdersDict(
    inputMfrVariableName: str, inputTemperatureVariableName: str, loop: _tp.Optional[_hlm.HydraulicLoop]
) -> _tp.Dict[str, str]:
    if not loop:
        return {
            "@temp": inputTemperatureVariableName,
            "@mfr": inputMfrVariableName,
        }

    loopName = loop.name.value

    return {
        "@temp": inputTemperatureVariableName,
        "@mfr": inputMfrVariableName,
        "@cp": _lnames.getHeatCapacityName(loopName),
        "@rho": _lnames.getDensityName(loopName),
    }


def _createOutputPlaceholdersDict(outputTemperatureVariableName, reverseInputTemperatureVariableName):
    placeholdersForPort = {"@temp": outputTemperatureVariableName, "@revtemp": reverseInputTemperatureVariableName}
    return placeholdersForPort


def _getLoop(
    hydraulicLoops: _hlm.HydraulicLoops, inputConnection: _cb.ConnectionBase
) -> _tp.Optional[_hlm.HydraulicLoop]:
    if not isinstance(inputConnection, _spc.SinglePipeConnection):
        return None

    hydraulicLoop = hydraulicLoops.getLoopForExistingConnection(inputConnection)
    return hydraulicLoop
