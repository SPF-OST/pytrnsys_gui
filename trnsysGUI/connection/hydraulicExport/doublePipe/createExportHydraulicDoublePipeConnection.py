import dataclasses as _dc

import trnsysGUI.connection.hydraulicExport.common as _com
import trnsysGUI.connection.hydraulicExport.doublePipe.doublePipeConnection as _hedpc
import trnsysGUI.massFlowSolver.networkModel as _mfn


@_dc.dataclass
class HydraulicDoublePipeConnection(_com.HydraulicConnectionBase):
    coldModelPipe: _mfn.Pipe
    hotModelPipe: _mfn.Pipe


def createModel(hydraulicConnection: HydraulicDoublePipeConnection) -> _hedpc.ExportHydraulicDoublePipeConnection:
    (
        coldInputTemperature,
        coldMassFlowRate,
        coldRevInputTemperature,
    ) = _com.getTemperatureMassFlowAndReverseTemperatureVariableNames(
        hydraulicConnection.displayName,
        hydraulicConnection.toAdjacentHasPiping,
        hydraulicConnection.fromAdjacentHasPiping,
        hydraulicConnection.coldModelPipe,
        _mfn.PortItemType.COLD,
    )

    # This assert is only used to satisfy MyPy, because we know that for double pipes, these have names.
    assert hydraulicConnection.coldModelPipe.name

    coldHydraulicExportPipe = _hedpc.Pipe(
        hydraulicConnection.coldModelPipe.name,
        _com.InputPort(coldInputTemperature, coldMassFlowRate),
        _com.OutputPort(coldRevInputTemperature),
    )

    (
        hotInputTemperature,
        hotMassFlowRate,
        hotRevInputTemperature,
    ) = _com.getTemperatureMassFlowAndReverseTemperatureVariableNames(
        hydraulicConnection.displayName,
        hydraulicConnection.fromAdjacentHasPiping,
        hydraulicConnection.toAdjacentHasPiping,
        hydraulicConnection.hotModelPipe,
        _mfn.PortItemType.HOT,
    )

    # This assert is only used to satisfy MyPy, because we know that for double pipes, these have names.
    assert hydraulicConnection.hotModelPipe.name

    hotHydraulicExportPipe = _hedpc.Pipe(
        hydraulicConnection.hotModelPipe.name,
        _com.InputPort(hotInputTemperature, hotMassFlowRate),
        _com.OutputPort(hotRevInputTemperature),
    )

    exportHydraulicConnection = _hedpc.ExportHydraulicDoublePipeConnection(
        hydraulicConnection.displayName, coldHydraulicExportPipe, hotHydraulicExportPipe
    )

    return exportHydraulicConnection
