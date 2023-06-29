import typing as _tp

import trnsysGUI.connection.hydraulicExport.singlePipe.singlePipeConnection as _spc
from trnsysGUI.connection import connectorsAndPipesExportHelpers as _helper


def exportDummyConnection(
    singlePipeConnection: _spc.ExportHydraulicSinglePipeConnection, unitNumber: int
) -> _tp.Tuple[str, int]:
    unitText = _helper.getIfThenElseUnit(
        unitNumber,
        singlePipeConnection.outputTemperatureVariableName,
        singlePipeConnection.initialOutputTemperatureVariableName,
        singlePipeConnection.pipe.inputPort.massFlowRateVariableName,
        singlePipeConnection.pipe.inputPort.inputTemperatureVariableName,
        singlePipeConnection.pipe.outputPort.inputTemperatureVariableName,
        canonicalMassFlowRate=singlePipeConnection.canonicalMassFlowRateVariableName,
        extraNewlines="\n\n",
    )

    nextUnitNumber = unitNumber + 1
    return unitText, nextUnitNumber
