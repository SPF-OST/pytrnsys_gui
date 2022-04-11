import pytrnsys.utils.result as _res
from trnsysGUI.BlockItem import BlockItem


def getPlaceholderValues(ddckFilePaths, trnsysObj) -> _res.Result[dict]:
    ddckPlaceHolderValuesDictionary = {}
    for component in trnsysObj:
        if isinstance(component, BlockItem) and component.hasDdckPlaceHolders():
            if not component.path:
                return _res.Error(
                    f"{component.displayName} doesn't have ddck template path"
                )
            split = component.path.split("\\")
            componentFilePath = split[-1]
            if componentFilePath not in ddckFilePaths:
                return _res.Error(
                    f"{componentFilePath} is not ddck template path"
                )
            inputDct = {}
            for inputPort in component.inputs:
                internalPiping = inputPort.parent.getInternalPiping()
                portItemsInternalRealNode = internalPiping.getPortItemsAndAdjacentRealNodeForGraphicalPortItem(
                    inputPort)
                portItems = [pr.portItem for pr in portItemsInternalRealNode]
                formattedPortItems = [f"{p.name}" for p in portItems]
                inputDct[formattedPortItems[0]] = {
                    "@temp": "T" + inputPort.connectionList[0].displayName,
                    "@mfr": "Mfr" + inputPort.connectionList[0].displayName}
            if not inputDct:
                return _res.Error(
                    f"{componentFilePath} doesn't have connection name for placeholder"
                )
            ddckPlaceHolderValuesDictionary[f"{componentFilePath}"] = inputDct
    return ddckPlaceHolderValuesDictionary
