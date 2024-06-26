import pathlib as _pl
import typing as _tp

import pytrnsys.utils.warnings as _warn
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


PlaceHolders = _tp.NewType("PlaceHolders", _tp.Mapping[str, str])
PlaceHoldersByQualifiedPortName = _tp.NewType("PlaceHoldersByQualifiedPortName", _tp.Mapping[str, PlaceHolders])
PlaceHoldersByComponentName = _tp.NewType(
    "PlaceHoldersByComponentName", _tp.Mapping[str, PlaceHoldersByQualifiedPortName]
)


def getPlaceholderValues(
    ddckDirNames: _tp.Sequence[str],
    blockItems: _tp.Sequence[_ip.HasInternalPiping],
    hydraulicLoops: _hlm.HydraulicLoops,
) -> _warn.ValueWithWarnings[PlaceHoldersByComponentName]:
    namesOfComponentsWithoutCorrespondingDdckDir = list[str]()
    allPlaceholders: dict[str, PlaceHoldersByQualifiedPortName] = {}
    for blockItem in blockItems:
        if not blockItem.hasDdckPlaceHolders():
            continue

        componentName = blockItem.getDisplayName()
        if componentName not in ddckDirNames:
            namesOfComponentsWithoutCorrespondingDdckDir.append(componentName)

        placeholdersForComponent: dict[str, PlaceHolders] = {}
        internalPiping = blockItem.getInternalPiping()
        for node in internalPiping.nodes:
            placeHoldersForNode = _getPlaceHoldersForNode(node, componentName, internalPiping, hydraulicLoops)

            placeholdersForComponent |= placeHoldersForNode

        allPlaceholders[componentName] = PlaceHoldersByQualifiedPortName(placeholdersForComponent)

    warning: str | None = None
    if namesOfComponentsWithoutCorrespondingDdckDir:
        warning = f"""\
The following components didn't have a corresponding directory of the same name in the ddck folder:

{"\t\n".join(namesOfComponentsWithoutCorrespondingDdckDir)}

This can happen if you're using a "template" ddck under a different name as its containing directory
(i.e. "PROJECT$ path\\to\\your\\template.ddck as different_name") - in which case you can ignore this warning
for that particular component - or it could indicate a missing ddck file.
"""

    placeHoldersByComponentName = PlaceHoldersByComponentName(allPlaceholders)
    allPlaceholdersWithWarnings = _warn.ValueWithWarnings.create(placeHoldersByComponentName, warning)

    return allPlaceholdersWithWarnings


def _getPlaceHoldersForNode(
    node: _mfn.Node, componentName: str, internalPiping: _ip.InternalPiping, hydraulicLoops: _hlm.HydraulicLoops
) -> PlaceHoldersByQualifiedPortName:
    placeHoldersForNode = {}
    for modelPortItem in node.getPortItems():
        nodeNameOrEmpty = node.name or ""
        qualifiedPortName = f"{nodeNameOrEmpty}{modelPortItem.name}"

        placeholdersForPort = _getPlaceholdersForPort(
            hydraulicLoops, componentName, internalPiping, node, modelPortItem
        )

        placeHoldersForNode[qualifiedPortName] = placeholdersForPort

    return PlaceHoldersByQualifiedPortName(placeHoldersForNode)


def _getPlaceholdersForPort(
    hydraulicLoops: _hlm.HydraulicLoops,
    displayName: str,
    internalPiping: _ip.InternalPiping,
    node: _mfn.Node,
    modelPortItem: _mfn.PortItem,
) -> PlaceHolders:
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
) -> PlaceHolders:
    if not loop:
        return PlaceHolders(
            {
                "@temp": inputTemperatureVariableName,
                "@mfr": inputMfrVariableName,
            }
        )

    loopName = loop.name.value

    return PlaceHolders(
        {
            "@temp": inputTemperatureVariableName,
            "@mfr": inputMfrVariableName,
            "@cp": _lnames.getHeatCapacityName(loopName),
            "@rho": _lnames.getDensityName(loopName),
        }
    )


def _createOutputPlaceholdersDict(
    outputTemperatureVariableName: str, reverseInputTemperatureVariableName: str
) -> PlaceHolders:
    placeholdersForPort = {"@temp": outputTemperatureVariableName, "@revtemp": reverseInputTemperatureVariableName}
    return PlaceHolders(placeholdersForPort)


def _getLoop(
    hydraulicLoops: _hlm.HydraulicLoops, inputConnection: _cb.ConnectionBase
) -> _tp.Optional[_hlm.HydraulicLoop]:
    if not isinstance(inputConnection, _spc.SinglePipeConnection):
        return None

    hydraulicLoop = hydraulicLoops.getLoopForExistingConnection(inputConnection)
    return hydraulicLoop
