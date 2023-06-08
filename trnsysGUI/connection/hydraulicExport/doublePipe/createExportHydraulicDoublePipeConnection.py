import dataclasses as _dc

import trnsysGUI.connection.connectorsAndPipesExportHelpers as _helpers
import trnsysGUI.connection.hydraulicExport.common as _com
import trnsysGUI.connection.hydraulicExport.doublePipe.doublePipeConnection as _hedpc
import trnsysGUI.doublePipePortItem as _dppi
import trnsysGUI.massFlowSolver.networkModel as _mfn


@_dc.dataclass
class HydraulicDoublePipeConnection(_com.HydraulicConnectionBase[_dppi.DoublePipePortItem]):
    coldModelPipe: _mfn.Pipe
    hotModelPipe: _mfn.Pipe


def createModel(hydraulicConnection: HydraulicDoublePipeConnection) -> _hedpc.ExportHydraulicDoublePipeConnection:
    coldInputTemperature = _helpers.getTemperatureVariableName(
        hydraulicConnection.toAdjacentHasPiping.hasInternalPiping,
        hydraulicConnection.toAdjacentHasPiping.sharedPort,
        _mfn.PortItemType.COLD,
    )
    coldMassFlowRate = _helpers.getInputMfrName(hydraulicConnection.displayName, hydraulicConnection.coldModelPipe)
    coldRevInputTemperature = _helpers.getTemperatureVariableName(
        hydraulicConnection.fromAdjacentHasPiping.hasInternalPiping,
        hydraulicConnection.fromAdjacentHasPiping.sharedPort,
        _mfn.PortItemType.COLD,
    )
    # This assert is only used to satisfy MyPy, because we know that for double pipes, these have names.
    assert hydraulicConnection.coldModelPipe.name

    coldHydraulicExportPipe = _hedpc.DoublePipe(
        hydraulicConnection.coldModelPipe.name,
        _com.InputPort(coldInputTemperature, coldMassFlowRate),
        _com.OutputPort(coldRevInputTemperature),
    )

    hotInputTemperature = _helpers.getTemperatureVariableName(
        hydraulicConnection.fromAdjacentHasPiping.hasInternalPiping,
        hydraulicConnection.fromAdjacentHasPiping.sharedPort,
        _mfn.PortItemType.HOT,
    )
    hotMassFlowRate = _helpers.getInputMfrName(hydraulicConnection.displayName, hydraulicConnection.hotModelPipe)
    hotRevInputTemperature = _helpers.getTemperatureVariableName(
        hydraulicConnection.toAdjacentHasPiping.hasInternalPiping,
        hydraulicConnection.toAdjacentHasPiping.sharedPort,
        _mfn.PortItemType.HOT,
    )
    # This assert is only used to satisfy MyPy, because we know that for double pipes, these have names.
    assert hydraulicConnection.hotModelPipe.name

    hotHydraulicExportPipe = _hedpc.DoublePipe(
        hydraulicConnection.hotModelPipe.name,
        _com.InputPort(hotInputTemperature, hotMassFlowRate),
        _com.OutputPort(hotRevInputTemperature),
    )

    exportHydraulicConnection = _hedpc.ExportHydraulicDoublePipeConnection(
        hydraulicConnection.displayName, coldHydraulicExportPipe, hotHydraulicExportPipe
    )

    return exportHydraulicConnection
