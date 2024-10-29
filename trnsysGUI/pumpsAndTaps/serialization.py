import dataclasses as _dc
import typing as _tp
import uuid as _uuid

import dataclasses_jsonschema as _dcj
import pytrnsys.utils.serialization as _ser

import trnsysGUI.blockItemModel as _bim
import trnsysGUI.blockItems.names as _bnames
import trnsysGUI.pumpsAndTaps.defaults as _defaults
import trnsysGUI.serialization as _gser


@_dc.dataclass
class BlockItemWithPrescribedMassFlowBaseModel(
    _ser.UpgradableJsonSchemaMixinVersion0
):
    blockItem: _bim.BlockItemBaseModel
    massFlowRateInKgPerH: float

    @classmethod
    @_tp.override
    def getVersion(cls) -> _uuid.UUID:
        return _uuid.UUID("e9fd1a0e-c00a-46e2-abfb-7381fa1b2e2d")


@_dc.dataclass
class _PumpModelVersion1(
    _ser.UpgradableJsonSchemaMixin, _gser.RequiredDecoderFieldsMixin
):  # pylint: disable=too-many-instance-attributes
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
    def getSupersededClass(
        cls,
    ) -> _tp.Type[_ser.UpgradableJsonSchemaMixinVersion0]:
        return _bim.BlockItemModelVersion1

    @classmethod
    @_tp.override
    def upgrade(
        cls, superseded: _ser.UpgradableJsonSchemaMixinVersion0
    ) -> "_PumpModelVersion1":
        assert isinstance(superseded, _bim.BlockItemModelVersion1)

        return _PumpModelVersion1(
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
class PumpModel(
    _gser.BlockItemUpgradableJsonSchemaMixin, _gser.RequiredDecoderFieldsMixin
):
    blockItemWithPrescribedMassFlow: BlockItemWithPrescribedMassFlowBaseModel

    inputPortId: int
    outputPortId: int

    @classmethod
    @_tp.override
    def getSupersededClass(
        cls,
    ) -> _tp.Type[_ser.UpgradableJsonSchemaMixinVersion0]:
        return _PumpModelVersion1

    @classmethod
    @_tp.override
    def upgrade(
        cls, superseded: _ser.UpgradableJsonSchemaMixinVersion0
    ) -> "PumpModel":
        assert isinstance(superseded, _PumpModelVersion1)

        blockItem = _bim.createBlockItemBaseModelFromLegacyModel(superseded)

        blockItemWithPrescribedMassFlow = (
            BlockItemWithPrescribedMassFlowBaseModel(
                blockItem, superseded.massFlowRateInKgPerH
            )
        )

        inputPortId = superseded.portsIdsIn[0]
        outputPortId = superseded.portsIdsOut[0]

        return PumpModel(
            superseded.BlockName,
            superseded.BlockDisplayName,
            blockItemWithPrescribedMassFlow,
            inputPortId,
            outputPortId,
        )

    @classmethod
    @_tp.override
    def getVersion(cls) -> _uuid.UUID:
        return _uuid.UUID("3d1e7f06-c7a6-49af-98b8-f593b34c5754")


@_dc.dataclass
class TerminalWithPrescribedMassFlowModel(
    _gser.BlockItemUpgradableJsonSchemaMixin, _gser.RequiredDecoderFieldsMixin
):
    blockItemWithPrescribedMassFlow: BlockItemWithPrescribedMassFlowBaseModel

    portId: int

    @classmethod
    @_tp.override
    def getSupersededClass(
        cls,
    ) -> _tp.Type[_ser.UpgradableJsonSchemaMixinVersion0]:
        return _bim.BlockItemModelVersion1

    @classmethod
    @_tp.override
    def upgrade(
        cls, superseded: _ser.UpgradableJsonSchemaMixinVersion0
    ) -> "TerminalWithPrescribedMassFlowModel":
        assert isinstance(superseded, _bim.BlockItemModelVersion1)

        blockItemBaseModel = _bim.createBlockItemBaseModelFromLegacyModel(
            superseded
        )

        prescribedMassFlowModel = BlockItemWithPrescribedMassFlowBaseModel(
            blockItemBaseModel,
            _defaults.DEFAULT_MASS_FLOW_RATE,
        )

        portId = (
            superseded.portsIdsIn[0]
            if superseded.BlockName == _bnames.TAP
            else superseded.portsIdsOut[0]
        )

        terminalModel = TerminalWithPrescribedMassFlowModel(
            superseded.BlockName,
            superseded.BlockDisplayName,
            prescribedMassFlowModel,
            portId,
        )

        return terminalModel

    @classmethod
    @_tp.override
    def getVersion(cls) -> _uuid.UUID:
        return _uuid.UUID("14afd9a0-54d6-44c7-b147-c79af3b782bb")
