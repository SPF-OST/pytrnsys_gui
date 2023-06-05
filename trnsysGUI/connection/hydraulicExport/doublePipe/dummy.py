import typing as _tp

import trnsysGUI.connection.connectorsAndPipesExportHelpers as _helper
import trnsysGUI.connection.hydraulicExport.doublePipe.doublePipeConnection as _dpc


def exportDummyConnection(
    doublePipeConnection: _dpc.ExportHydraulicDoublePipeConnection,
    unitNumber: int,
    shallDefineCanonicalMassFlowVariables: bool,
) -> _tp.Tuple[str, int]:
    coldIfThenElseUnitNumber = unitNumber
    coldPipe = doublePipeConnection.coldPipe
    coldUnitText = _getIfThenElseUnitText(
        doublePipeConnection, coldPipe, coldIfThenElseUnitNumber, shallDefineCanonicalMassFlowVariables
    )

    hotIfThenElseUnitNumber = unitNumber + 1
    hotPipe = doublePipeConnection.hotPipe
    hotUnitText = _getIfThenElseUnitText(
        doublePipeConnection, hotPipe, hotIfThenElseUnitNumber, shallDefineCanonicalMassFlowVariables
    )

    dummyConnectionText = f"""\
! BEGIN {doublePipeConnection.displayName}
! cold pipe
{coldUnitText}

! hot pipe
{hotUnitText}
! END {doublePipeConnection.displayName}


"""

    nextFreeUnitNumber = unitNumber + 2

    return dummyConnectionText, nextFreeUnitNumber


def _getIfThenElseUnitText(
    doublePipeConnection: _dpc.ExportHydraulicDoublePipeConnection,
    pipe: _dpc.DoublePipe,
    unitNumber: int,
    shallDefineCanonicalMassFlowVariables: bool,
) -> str:
    canonicalMassFlowRateVariableName: _tp.Optional[str] = None
    if shallDefineCanonicalMassFlowVariables:
        canonicalMassFlowRateVariableName = doublePipeConnection.getCanonicalMassFlowRateVariableName(pipe)

    outputTemperatureVariableName = doublePipeConnection.getOutputTemperatureVariableName(pipe)
    initialOutputTemperatureVariableName = doublePipeConnection.getInitialOutputTemperatureVariableName(pipe)

    unitText = _helper.getIfThenElseUnit(
        unitNumber,
        outputTemperatureVariableName,
        initialOutputTemperatureVariableName,
        pipe.inputPort.massFlowRateVariableName,
        pipe.inputPort.inputTemperatureVariableName,
        pipe.outputPort.inputTemperatureVariableName,
        canonicalMassFlowRate=canonicalMassFlowRateVariableName,
        extraNewlines="",
    )

    return unitText
