import pathlib as _pl
import typing as _tp

import pytrnsys.utils.result as _res
import trnsysGUI.BlockItem as _bi
import trnsysGUI.connection.names as _cnames
import trnsysGUI.internalPiping as _ip
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
                    inputConnection = graphicalPortItem.getConnection()

                    inputTemperatureVariableName = _cnames.getTemperatureVariableName(inputConnection, modelPortItem.type)
                    inputMfrVariableName = _cnames.getInputMassFlowVariableName(graphicalPortItem, modelPortItem.type)

                    placeholders[modelPortItem.name] = {
                        "@temp": inputTemperatureVariableName,
                        "@mfr": inputMfrVariableName
                    }

        allPlaceholders[componentName] = placeholders

    return allPlaceholders
