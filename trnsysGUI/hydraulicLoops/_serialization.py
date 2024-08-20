import dataclasses as _dc
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


@_dc.dataclass
class HydraulicLoop(_ser.UpgradableJsonSchemaMixin):
    name: str
    hasUserDefinedName: bool
    fluidName: str
    connectionsDefinitionMode: _cdm.ConnectionsDefinitionMode
    connectionsTrnsysId: _tp.Sequence[int]

    @classmethod
    def upgrade(cls, superseded: _ser.UpgradableJsonSchemaMixinVersion0) -> "HydraulicLoop":
        assert isinstance(superseded, HydraulicLoopVersion1)

        connectionsEditMode = (
            _cdm.ConnectionsDefinitionMode.LOOP_WIDE_DEFAULTS
            if superseded.useLoopWideDefaults
            else _cdm.ConnectionsDefinitionMode.INDIVIDUAL
        )

        return HydraulicLoop(
            superseded.name,
            superseded.hasUserDefinedName,
            superseded.fluidName,
            connectionsEditMode,
            superseded.connectionsTrnsysId,
        )

    @classmethod
    def getSupersededClass(cls) -> _tp.Type[_ser.UpgradableJsonSchemaMixin]:
        return HydraulicLoopVersion1

    @classmethod
    def getVersion(cls) -> _uuid.UUID:
        return _uuid.UUID("c743e29e-faaa-4e84-bf0f-6a10299097ed")
