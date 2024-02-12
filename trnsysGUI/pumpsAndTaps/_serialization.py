import dataclasses as _dc
import typing as _tp
import uuid as _uuid

import dataclasses_jsonschema as _dcj

from pytrnsys.utils import serialization as _ser
from trnsysGUI import blockItemModel as _bim
from . import _defaults


@_dc.dataclass
class BlockItemBaseModel(_ser.UpgradableJsonSchemaMixinVersion0):  # pylint: disable=too-many-instance-attributes
    BlockName: str  # pylint: disable=invalid-name
    BlockDisplayName: str  # pylint: disable=invalid-name
    blockPosition: _tp.Tuple[float, float]
    Id: int  # pylint: disable=invalid-name,duplicate-code # 1
    trnsysId: int
    flippedH: bool
    flippedV: bool
    rotationN: int

    @classmethod
    @_tp.override
    def getVersion(cls) -> _uuid.UUID:
        return _uuid.UUID("4f64dfcd-a0cf-45fd-a788-ff774c5b608f")


@_dc.dataclass
class BlockItemWithPrescribedMassFlowBaseModel(_ser.UpgradableJsonSchemaMixinVersion0):
    blockItem: BlockItemBaseModel
    massFlowRateInKgPerH: float

    @classmethod
    @_tp.override
    def getVersion(cls) -> _uuid.UUID:
        return _uuid.UUID("e9fd1a0e-c00a-46e2-abfb-7381fa1b2e2d")


@_dc.dataclass
class PumpModelVersion1(_ser.UpgradableJsonSchemaMixin):  # pylint: disable=too-many-instance-attributes
    BlockName: str  # pylint: disable=invalid-name
    BlockDisplayName: str  # pylint: disable=invalid-name
    blockPosition: _tp.Tuple[float, float]
    Id: int  # pylint: disable=invalid-name,duplicate-code # 1
    trnsysId: int
    portsIdsIn: _tp.List[int]
    portsIdsOut: _tp.List[int]
    flippedH: bool
    flippedV: bool
    rotationN: int

    massFlowRateInKgPerH: float

    @classmethod
    @_tp.override
    def getSupersededClass(cls) -> _tp.Type[_ser.UpgradableJsonSchemaMixinVersion0]:
        return _bim.BlockItemModel

    @classmethod
    @_tp.override
    def upgrade(cls, superseded: _ser.UpgradableJsonSchemaMixinVersion0) -> "PumpModelVersion1":
        assert isinstance(superseded, _bim.BlockItemModel)

        return PumpModelVersion1(
            superseded.BlockName,
            superseded.BlockDisplayName,
            superseded.blockPosition,
            superseded.Id,
            superseded.trnsysId,
            superseded.portsIdsIn,
            superseded.portsIdsOut,
            superseded.flippedH,
            superseded.flippedV,
            superseded.rotationN,
            _defaults.DEFAULT_MASS_FLOW_RATE,
        )

    @classmethod
    @_tp.override
    def getVersion(cls) -> _uuid.UUID:
        return _uuid.UUID("9552365f-ef11-4fac-ba35-644e94b54088")


@_dc.dataclass
class PumpModel(_ser.UpgradableJsonSchemaMixin):
    blockItemWithPrescribedMassFlow: BlockItemWithPrescribedMassFlowBaseModel

    inputPortId: int
    outputPortId: int

    @classmethod
    @_tp.override
    def from_dict(
        cls,  # pylint: disable = duplicate-code 2
        data: _dcj.JsonDict,  # pylint: disable = duplicate-code 2
        validate=True,
        validate_enums: bool = True,
        schema_type: _dcj.SchemaType = _dcj.DEFAULT_SCHEMA_TYPE,  # /NOSONAR
    ) -> "PumpModel":
        pumpModel = super().from_dict(data, validate, validate_enums, schema_type)
        return _tp.cast(PumpModel, pumpModel)

    @_tp.override
    def to_dict(
        self,
        omit_none: bool = True,
        validate: bool = False,
        validate_enums: bool = True,  # pylint: disable=duplicate-code 2
        schema_type: _dcj.SchemaType = _dcj.DEFAULT_SCHEMA_TYPE,  # /NOSONAR
    ) -> _dcj.JsonDict:
        data = super().to_dict(omit_none, validate, validate_enums, schema_type)
        data[".__BlockDict__"] = True
        return data

    @classmethod
    @_tp.override
    def getSupersededClass(cls) -> _tp.Type[_ser.UpgradableJsonSchemaMixinVersion0]:
        return PumpModelVersion1

    @classmethod
    @_tp.override
    def upgrade(cls, superseded: _ser.UpgradableJsonSchemaMixinVersion0) -> "PumpModel":
        assert isinstance(superseded, PumpModelVersion1)

        blockItem = BlockItemBaseModel(
            superseded.BlockName,
            superseded.BlockDisplayName,
            superseded.blockPosition,
            superseded.Id,
            superseded.trnsysId,
            superseded.flippedH,
            superseded.flippedV,
            superseded.rotationN,
        )

        blockItemWithPrescribedMassFlow = BlockItemWithPrescribedMassFlowBaseModel(
            blockItem, superseded.massFlowRateInKgPerH
        )

        inputPortId = superseded.portsIdsIn[0]
        outputPortId = superseded.portsIdsOut[0]

        return PumpModel(
            blockItemWithPrescribedMassFlow,
            inputPortId,
            outputPortId,
        )

    @classmethod
    @_tp.override
    def getVersion(cls) -> _uuid.UUID:
        return _uuid.UUID("3d1e7f06-c7a6-49af-98b8-f593b34c5754")


@_dc.dataclass
class TerminalWithPrescribedMassFlowModel(_ser.UpgradableJsonSchemaMixinVersion0):
    blockItemWithPrescribedMassFlow: BlockItemWithPrescribedMassFlowBaseModel

    portId: int

    @classmethod
    @_tp.override
    def from_dict(
        cls,  # pylint: disable = duplicate-code 3
        data: _dcj.JsonDict,  # pylint: disable = duplicate-code 3
        validate=True,
        validate_enums: bool = True,
        schema_type: _dcj.SchemaType = _dcj.DEFAULT_SCHEMA_TYPE,  # /NOSONAR
    ) -> "TerminalWithPrescribedMassFlowModel":
        pumpModel = super().from_dict(data, validate, validate_enums, schema_type)
        return _tp.cast(TerminalWithPrescribedMassFlowModel, pumpModel)

    @_tp.override
    def to_dict(
        self,
        omit_none: bool = True,
        validate: bool = False,
        validate_enums: bool = True,  # pylint: disable=duplicate-code 3
        schema_type: _dcj.SchemaType = _dcj.DEFAULT_SCHEMA_TYPE,  # /NOSONAR
    ) -> _dcj.JsonDict:
        data = super().to_dict(omit_none, validate, validate_enums, schema_type)
        data[".__BlockDict__"] = True
        return data

    @classmethod
    @_tp.override
    def getVersion(cls) -> _uuid.UUID:
        return _uuid.UUID("14afd9a0-54d6-44c7-b147-c79af3b782bb")
