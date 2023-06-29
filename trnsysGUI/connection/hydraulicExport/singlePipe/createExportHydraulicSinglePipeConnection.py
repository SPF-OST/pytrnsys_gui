import dataclasses as _dc

import trnsysGUI.connection.hydraulicExport.common as _com
import trnsysGUI.connection.hydraulicExport.singlePipe.singlePipeConnection as _hespc
import trnsysGUI.massFlowSolver.networkModel as _mfn


@_dc.dataclass
class HydraulicSinglePipeConnection(_com.HydraulicConnectionBase):
    modelPipe: _mfn.Pipe


def createExportHydraulicConnection(
    hydraulicConnection: HydraulicSinglePipeConnection,
) -> _hespc.ExportHydraulicSinglePipeConnection:
    (
        inputTemperature,
        massFlowRate,
        revInputTemperature,
    ) = _com.getTemperatureMassFlowAndReverseTemperatureVariableNames(
        hydraulicConnection.displayName,
        hydraulicConnection.fromAdjacentHasPiping,
        hydraulicConnection.toAdjacentHasPiping,
        hydraulicConnection.modelPipe,
        _mfn.PortItemType.STANDARD,
    )

    # single pipe should not have a name for their model pipes
    assert not hydraulicConnection.modelPipe.name

    hydraulicExportPipe = _hespc.Pipe(
        _com.InputPort(inputTemperature, massFlowRate),
        _com.OutputPort(revInputTemperature),
    )

    exportHydraulicConnection = _hespc.ExportHydraulicSinglePipeConnection(
        hydraulicConnection.displayName, hydraulicExportPipe
    )

    return exportHydraulicConnection
