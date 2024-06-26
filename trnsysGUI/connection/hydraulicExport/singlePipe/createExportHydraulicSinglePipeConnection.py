import dataclasses as _dc

import trnsysGUI.connection.hydraulicExport.common as _com
import trnsysGUI.connection.hydraulicExport.singlePipe.dummy as _he
import trnsysGUI.connection.hydraulicExport.singlePipe.singlePipeConnection as _hespc
import trnsysGUI.internalPiping as _ip
import trnsysGUI.massFlowSolver.networkModel as _mfn
import trnsysGUI.singlePipePortItem as _spi


@_dc.dataclass
class HydraulicSinglePipeConnection(_com.HydraulicConnectionBase):
    modelPipe: _mfn.TwoNeighboursBase


def createExportHydraulicSinglePipeConnection(
    hasInternalPiping: _ip.HasInternalPiping,
    fromPort: _spi.SinglePipePortItem,
    toPort: _spi.SinglePipePortItem,
    twoNeighboursBaseModel: _mfn.TwoNeighboursBase,
) -> _hespc.ExportHydraulicSinglePipeConnection:
    hydraulicConnection = HydraulicSinglePipeConnection(
        hasInternalPiping.getDisplayName(),
        _com.getAdjacentHasInternalPiping(hasInternalPiping, fromPort),
        _com.getAdjacentHasInternalPiping(hasInternalPiping, toPort),
        twoNeighboursBaseModel,
    )

    hydraulicExportConnection = _createFromHydraulicConnection(hydraulicConnection)

    return hydraulicExportConnection


def _createFromHydraulicConnection(
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


def exportDummySinglePipeConnection(
    hasInternalPiping: _ip.HasInternalPiping,
    startingUnit: int,
    fromPort: _spi.SinglePipePortItem,
    toPort: _spi.SinglePipePortItem,
    twoNeighboursBaseModel: _mfn.TwoNeighboursBase,
) -> tuple[str, int]:
    hydraulicExportConnection = createExportHydraulicSinglePipeConnection(
        hasInternalPiping, fromPort, toPort, twoNeighboursBaseModel
    )

    unitNumber = startingUnit
    return _he.exportDummyConnection(hydraulicExportConnection, unitNumber)
