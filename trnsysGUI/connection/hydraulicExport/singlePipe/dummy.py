import typing as _tp

import trnsysGUI.connection.hydraulicExport.singlePipe.singlePipeConnection as _spc
from trnsysGUI import temperatures as _temps, globalNames as _gnames
from trnsysGUI.connection import connectorsAndPipesExportHelpers as _helper
from trnsysGUI.massFlowSolver import names as _mnames


def exportDummyConnection(
    singlePipeConnection: _spc.ExportHydraulicSinglePipeConnection, unitNumber: int
) -> _tp.Tuple[str, int]:
    canonicalMassFlowRateVariableName = _mnames.getCanonicalMassFlowVariableName(
        componentDisplayName=singlePipeConnection.displayName, pipeName=None
    )

    outputTemperatureVariableName = _temps.getTemperatureVariableName(
        shallRenameOutputInHydraulicFile=False, componentDisplayName=singlePipeConnection.displayName, nodeName=None
    )

    initialOutputTemperatureVariableName = _gnames.SinglePipes.INITIAL_TEMPERATURE

    unitText = _helper.getIfThenElseUnit(
        unitNumber,
        outputTemperatureVariableName,
        initialOutputTemperatureVariableName,
        singlePipeConnection.pipe.inputPort.massFlowRateVariableName,
        singlePipeConnection.pipe.inputPort.inputTemperatureVariableName,
        singlePipeConnection.pipe.outputPort.inputTemperatureVariableName,
        canonicalMassFlowRate=canonicalMassFlowRateVariableName,
        extraNewlines=r"\n\n",
    )

    return unitText, unitNumber
