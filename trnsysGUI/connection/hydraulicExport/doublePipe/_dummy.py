import typing as _tp

import trnsysGUI.connectorsAndPipesExportHelpers as _helper
from . import doublePipeConnection as _dpc


def exportDummyConnection(doublePipeConnection: _dpc.DoublePipeConnection, unitNumber: int) -> _tp.Tuple[str, int]:
    coldIfThenElseUnitNumber = unitNumber
    coldPipe = doublePipeConnection.coldPipe
    coldUnitText = _getIfThenElseUnitText(doublePipeConnection, coldPipe, coldIfThenElseUnitNumber)

    hotIfThenElseUnitNumber = unitNumber + 1
    hotPipe = doublePipeConnection.hotPipe
    hotUnitText = _getIfThenElseUnitText(doublePipeConnection, hotPipe, hotIfThenElseUnitNumber)

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
    doublePipeConnection: _dpc.DoublePipeConnection,
    pipe: _dpc.SinglePipe,
    unitNumber: int,
) -> str:
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
