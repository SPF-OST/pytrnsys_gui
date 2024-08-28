import dataclasses as _dc
import enum as _enum
import typing as _tp
import uuid as _uuid

import pytrnsys.utils.serialization as _ser

from . import connectionsDefinitionMode as _cdm


@_dc.dataclass
class Variable(_ser.UpgradableJsonSchemaMixinVersion0):
    name: str

    @classmethod
    def getVersion(cls) -> _uuid.UUID:
        return _uuid.UUID("3196024b-6775-42bc-92d2-e11d60c64bac")


@_dc.dataclass(frozen=True, eq=False)
class Fluid(_ser.UpgradableJsonSchemaMixinVersion0):
    name: str
    specificHeatCapacityInJPerKgK: _tp.Union[Variable, float]  # /NOSONAR
    densityInKgPerM3: _tp.Union[Variable, float]  # /NOSONAR

    @classmethod
    def getVersion(cls) -> _uuid.UUID:
        return _uuid.UUID("5b1d8eb8-e9c0-4c6a-b14f-0a7216b60132")


@_dc.dataclass
class HydraulicLoopVersion0(_ser.UpgradableJsonSchemaMixinVersion0):
    name: str
    hasUserDefinedName: bool
    fluidName: str
    connectionsTrnsysId: _tp.Sequence[int]

    @classmethod
    def getVersion(cls) -> _uuid.UUID:
        return _uuid.UUID("0047cab1-dd67-42ee-af45-5e5d30d97a92")


@_dc.dataclass
class HydraulicLoopVersion1(_ser.UpgradableJsonSchemaMixin):
    name: str
    hasUserDefinedName: bool
    fluidName: str
    useLoopWideDefaults: bool
    connectionsTrnsysId: _tp.Sequence[int]

    @classmethod
    def upgrade(cls, superseded: _ser.UpgradableJsonSchemaMixinVersion0) -> "HydraulicLoopVersion1":
        assert isinstance(superseded, HydraulicLoopVersion0)

        useLoopWideDefaults = False

        return HydraulicLoopVersion1(
            superseded.name,
            superseded.hasUserDefinedName,
            superseded.fluidName,
            useLoopWideDefaults,
            superseded.connectionsTrnsysId,
        )

    @classmethod
    def getSupersededClass(cls) -> _tp.Type[_ser.UpgradableJsonSchemaMixinVersion0]:
        return HydraulicLoopVersion0

    @classmethod
    def getVersion(cls) -> _uuid.UUID:
        return _uuid.UUID("990b8023-eb4b-408e-8d54-23caa5916b2a")


class _ConnectionsDefinitionModeVersion0(_enum.Enum):
    INDIVIDUAL = _enum.auto()
    LOOP_WIDE_DEFAULTS = _enum.auto()
    DUMMY_PIPES = _enum.auto()

    def upgrade(self) -> _cdm.ConnectionsDefinitionMode:
        if self == self.INDIVIDUAL:
            return _cdm.ConnectionsDefinitionMode.INDIVIDUAL

        if self == self.LOOP_WIDE_DEFAULTS:
            return _cdm.ConnectionsDefinitionMode.LOOP_WIDE_DEFAULTS

        if self == self.DUMMY_PIPES:
            return _cdm.ConnectionsDefinitionMode.DUMMY_PIPES

        raise ValueError("Unknown connections definition mode.", self)


@_dc.dataclass
class HydraulicLoopVersion2(_ser.UpgradableJsonSchemaMixin):
    name: str
    hasUserDefinedName: bool
    fluidName: str
    connectionsDefinitionMode: _ConnectionsDefinitionModeVersion0
    connectionsTrnsysId: _tp.Sequence[int]

    @classmethod
    def upgrade(cls, superseded: _ser.UpgradableJsonSchemaMixinVersion0) -> "HydraulicLoopVersion2":
        assert isinstance(superseded, HydraulicLoopVersion1)

        connectionsDefinitionMode = (
            _ConnectionsDefinitionModeVersion0.LOOP_WIDE_DEFAULTS
            if superseded.useLoopWideDefaults
            else _ConnectionsDefinitionModeVersion0.INDIVIDUAL
        )

        return HydraulicLoopVersion2(
            superseded.name,
            superseded.hasUserDefinedName,
            superseded.fluidName,
            connectionsDefinitionMode,
            superseded.connectionsTrnsysId,
        )

    @classmethod
    def getSupersededClass(cls) -> _tp.Type[_ser.UpgradableJsonSchemaMixin]:
        return HydraulicLoopVersion1

    @classmethod
    def getVersion(cls) -> _uuid.UUID:
        return _uuid.UUID("c743e29e-faaa-4e84-bf0f-6a10299097ed")


@_dc.dataclass
class HydraulicLoop(_ser.UpgradableJsonSchemaMixin):
    name: str
    hasUserDefinedName: bool
    fluidName: str
    connectionsDefinitionMode: _cdm.ConnectionsDefinitionMode
    connectionsTrnsysId: _tp.Sequence[int]

    @classmethod
    def upgrade(cls, superseded: _ser.UpgradableJsonSchemaMixinVersion0) -> "HydraulicLoop":
        assert isinstance(superseded, HydraulicLoopVersion2)

        return HydraulicLoop(
            superseded.name,
            superseded.hasUserDefinedName,
            superseded.fluidName,
            superseded.connectionsDefinitionMode.upgrade(),
            superseded.connectionsTrnsysId,
        )

    @classmethod
    def getSupersededClass(cls) -> _tp.Type[_ser.UpgradableJsonSchemaMixin]:
        return HydraulicLoopVersion2

    @classmethod
    def getVersion(cls) -> _uuid.UUID:
        return _uuid.UUID("1e16cd15-83b9-46fa-ac63-11b2b2209af1")
