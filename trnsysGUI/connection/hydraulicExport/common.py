import abc as _abc
import dataclasses as _dc
import typing as _tp

import trnsysGUI.PortItemBase as _pib
import trnsysGUI.connection.connectorsAndPipesExportHelpers as _helpers
import trnsysGUI.connection.values as _values
import trnsysGUI.internalPiping as _ip
import trnsysGUI.massFlowSolver.networkModel as _mfn


@_dc.dataclass
class PortBase(_abc.ABC):
    inputTemperatureVariableName: str


@_dc.dataclass
class InputPort(PortBase):
    massFlowRateVariableName: str


@_dc.dataclass
class OutputPort(PortBase):
    pass


_T = _tp.TypeVar("_T")


@_dc.dataclass
class GenericConnection(_tp.Generic[_T]):
    hydraulicConnection: _T
    lengthInM: _values.Value
    shallBeSimulated: bool


@_dc.dataclass
class AdjacentHasInternalPiping:
    """A "component" (i.e. a connection or block item) that shares a port with us"""

    hasInternalPiping: _ip.HasInternalPiping
    sharedPort: _pib.PortItemBase


def getAdjacentConnection(
    port: _pib.PortItemBase,
) -> AdjacentHasInternalPiping:
    return AdjacentHasInternalPiping(port.getConnection(), port)


def getAdjacentBlockItem(port: _pib.PortItemBase) -> AdjacentHasInternalPiping:
    return AdjacentHasInternalPiping(port.parent, port)


def getAdjacentHasInternalPiping(
    hasInternalPiping: _ip.HasInternalPiping, port: _pib.PortItemBase
) -> AdjacentHasInternalPiping:
    connection = port.getConnection()
    blockItem = port.parent

    if hasInternalPiping is connection:
        return AdjacentHasInternalPiping(blockItem, port)

    if hasInternalPiping is blockItem:
        return AdjacentHasInternalPiping(connection, port)

    raise ValueError("Port doesn't belong to `hasInternalPiping`.")


@_dc.dataclass
class HydraulicConnectionBase(_abc.ABC):
    displayName: str
    fromAdjacentHasPiping: AdjacentHasInternalPiping
    toAdjacentHasPiping: AdjacentHasInternalPiping


def getTemperatureMassFlowAndReverseTemperatureVariableNames(
    displayName: str,
    fromAdjacentHasPiping: AdjacentHasInternalPiping,
    toAdjacentHasPiping: AdjacentHasInternalPiping,
    pipe: _mfn.TwoNeighboursBase,
    portItemType: _mfn.PortItemType,
):
    inputTemperature = _helpers.getTemperatureVariableName(
        fromAdjacentHasPiping.hasInternalPiping,
        fromAdjacentHasPiping.sharedPort,
        portItemType,
    )

    massFlowRate = _helpers.getInputMfrName(displayName, pipe)

    revInputTemperature = _helpers.getTemperatureVariableName(
        toAdjacentHasPiping.hasInternalPiping,
        toAdjacentHasPiping.sharedPort,
        portItemType,
    )

    return inputTemperature, massFlowRate, revInputTemperature
