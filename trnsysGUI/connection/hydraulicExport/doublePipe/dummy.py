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

    coldCanonicalMassFlowRateVariableName: _tp.Optional[str] = None
    if shallDefineCanonicalMassFlowVariables:
        coldCanonicalMassFlowRateVariableName = doublePipeConnection.coldCanonicalMassFlowRateVariableName

    coldUnitText = _helper.getIfThenElseUnit(
        coldIfThenElseUnitNumber,
        doublePipeConnection.coldOutputTemperatureVariableName,
        doublePipeConnection.initialColdOutputTemperatureVariableName,
        coldPipe.inputPort.massFlowRateVariableName,
        coldPipe.inputPort.inputTemperatureVariableName,
        coldPipe.outputPort.inputTemperatureVariableName,
        canonicalMassFlowRate=coldCanonicalMassFlowRateVariableName,
        extraNewlines="",
    )

    hotIfThenElseUnitNumber = unitNumber + 1
    hotPipe = doublePipeConnection.hotPipe

    hotCanonicalMassFlowRateVariableName: _tp.Optional[str] = None
    if shallDefineCanonicalMassFlowVariables:
        hotCanonicalMassFlowRateVariableName = doublePipeConnection.hotCanonicalMassFlowRateVariableName

    hotUnitText = _helper.getIfThenElseUnit(
        hotIfThenElseUnitNumber,
        doublePipeConnection.hotOutputTemperatureVariableName,
        doublePipeConnection.initialHotOutputTemperatureVariableName,
        hotPipe.inputPort.massFlowRateVariableName,
        hotPipe.inputPort.inputTemperatureVariableName,
        hotPipe.outputPort.inputTemperatureVariableName,
        canonicalMassFlowRate=hotCanonicalMassFlowRateVariableName,
        extraNewlines="",
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
