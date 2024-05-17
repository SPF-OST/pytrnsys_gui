import dataclasses as _dc

import trnsysGUI.connection.hydraulicExport.common as _com
from trnsysGUI import internalPiping as _ip
from trnsysGUI import singlePipePortItem as _spi
from trnsysGUI.connection.hydraulicExport import common as _hecom
from trnsysGUI.connection.hydraulicExport.singlePipe import dummy as _he
from trnsysGUI.connection.hydraulicExport.singlePipe import singlePipeConnection as _hespc
from trnsysGUI.massFlowSolver import networkModel as _mfn


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
        _hecom.getAdjacentHasInternalPiping(hasInternalPiping, fromPort),
        _hecom.getAdjacentHasInternalPiping(hasInternalPiping, toPort),
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
