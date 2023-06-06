import dataclasses as _dc

import trnsysGUI.connection.connectorsAndPipesExportHelpers as _helpers
import trnsysGUI.connection.hydraulicExport.doublePipe.doublePipeConnection as _hedpc
import trnsysGUI.doublePipePortItem as _dppi
import trnsysGUI.massFlowSolver.networkModel as _mfn


@_dc.dataclass
class HydraulicConnection:
    displayName: str
    fromPort: _dppi.DoublePipePortItem
    toPort: _dppi.DoublePipePortItem
    coldModelPipe: _mfn.Pipe
    hotModelPipe: _mfn.Pipe


def createModel(hydraulicConnection: HydraulicConnection) -> _hedpc.HydraulicDoublePipeConnection:
    coldInputTemperature = _helpers.getTemperatureVariableName(
        hydraulicConnection.toPort.parent, hydraulicConnection.toPort, _mfn.PortItemType.COLD
    )
    coldMassFlowRate = _helpers.getInputMfrName(hydraulicConnection.displayName, hydraulicConnection.coldModelPipe)
    coldRevInputTemperature = _helpers.getTemperatureVariableName(
        hydraulicConnection.fromPort.parent, hydraulicConnection.fromPort, _mfn.PortItemType.COLD
    )
    # This assert is only used to satisfy MyPy, because we know that for double pipes, these have names.
    assert hydraulicConnection.coldModelPipe.name and hydraulicConnection.hotModelPipe.name

    coldHydraulicExportPipe = _hedpc.SinglePipe(
        hydraulicConnection.coldModelPipe.name,
        _hedpc.InputPort(coldInputTemperature, coldMassFlowRate),
        _hedpc.OutputPort(coldRevInputTemperature),
    )

    hotInputTemperature = _helpers.getTemperatureVariableName(
        hydraulicConnection.fromPort.parent, hydraulicConnection.fromPort, _mfn.PortItemType.HOT
    )
    hotMassFlowRate = _helpers.getInputMfrName(hydraulicConnection.displayName, hydraulicConnection.hotModelPipe)
    hotRevInputTemperature = _helpers.getTemperatureVariableName(
        hydraulicConnection.toPort.parent, hydraulicConnection.toPort, _mfn.PortItemType.HOT
    )
    # This assert is only used to satisfy MyPy, because we know that for double pipes, these have names.
    assert hydraulicConnection.hotModelPipe.name

    hotHydraulicExportPipe = _hedpc.SinglePipe(
        hydraulicConnection.hotModelPipe.name,
        _hedpc.InputPort(hotInputTemperature, hotMassFlowRate),
        _hedpc.OutputPort(hotRevInputTemperature),
    )

    hydraulicConnectionModel = _hedpc.HydraulicDoublePipeConnection(
        hydraulicConnection.displayName, coldHydraulicExportPipe, hotHydraulicExportPipe
    )

    return hydraulicConnectionModel
