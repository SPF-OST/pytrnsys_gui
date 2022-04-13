import typing as _tp
import pathlib as _pl

import pytrnsys.utils.result as _res
from trnsysGUI.BlockItem import BlockItem


def getPlaceholderValues(ddckDirNames: _tp.Sequence[str], trnsysObjects) -> _res.Result[dict]:
    ddckPlaceHolderValuesDictionary = {}
    for component in trnsysObjects:
        if not isinstance(component, BlockItem) or not component.hasDdckPlaceHolders():
            continue

        if not component.path:
            return _res.Error(
                f"{component.displayName} doesn't have ddck template path"
            )

        componentPath = _pl.Path(component.path)
        componentName = componentPath.stem
        if componentName not in ddckDirNames:
            return _res.Error(
                f"{componentName} is not a ddck template path"
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
                f"{componentName} doesn't have connection name for placeholder"
            )
        ddckPlaceHolderValuesDictionary[componentName] = inputDct

    return ddckPlaceHolderValuesDictionary
