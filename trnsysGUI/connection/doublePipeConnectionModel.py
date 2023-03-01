import dataclasses as _dc
import typing as _tp
import uuid as _uuid

import dataclasses_jsonschema as _dcj

from pytrnsys.utils import serialization as _ser


@_dc.dataclass
class DoublePipeConnectionModelVersion0(
    _ser.UpgradableJsonSchemaMixinVersion0):  # pylint: disable=too-many-instance-attributes
    connectionId: int
    name: str
    id: int  # pylint: disable=invalid-name
    childIds: _tp.List[int]
    segmentsCorners: _tp.List[_tp.Tuple[float, float]]
    labelPos: _tp.Tuple[float, float]
    massFlowLabelPos: _tp.Tuple[float, float]
    fromPortId: int
    toPortId: int
    trnsysId: int

    @classmethod
    def getVersion(cls) -> _uuid.UUID:
        return _uuid.UUID("0810c9ea-85df-4431-bb40-3190c25c9161")


@_dc.dataclass
class DoublePipeConnectionModel(_ser.UpgradableJsonSchemaMixinVersion0):  # pylint: disable=too-many-instance-attributes
    connectionId: int
    name: str
    id: int  # pylint: disable=invalid-name
    childIds: _tp.List[int]
    segmentsCorners: _tp.List[_tp.Tuple[float, float]]
    labelPos: _tp.Tuple[float, float]
    massFlowLabelPos: _tp.Tuple[float, float]
    fromPortId: int
    toPortId: int
    trnsysId: int

    # @classmethod
    # def getSupersededClass(cls) -> _tp.Type[_ser.UpgradableJsonSchemaMixinVersion0]:
    #     return DoublePipeConnectionModelVersion0

    @classmethod
    def from_dict(
            cls,
            data: _dcj.JsonDict,  # pylint: disable=duplicate-code  # 1
            validate=True,
            validate_enums: bool = True,
    ) -> "DoublePipeConnectionModel":
        data.pop(".__ConnectionDict__")
        doublePipeConnectionModel = super().from_dict(data, validate, validate_enums)
        return _tp.cast(DoublePipeConnectionModel, doublePipeConnectionModel)

    def to_dict(
            self,
            omit_none: bool = True,
            validate: bool = False,
            validate_enums: bool = True,  # pylint: disable=duplicate-code # 1
    ) -> _dcj.JsonDict:
        data = super().to_dict(omit_none, validate, validate_enums)
        data[".__ConnectionDict__"] = True
        return data

    @classmethod
    def getVersion(cls) -> _uuid.UUID:
        return _uuid.UUID('bdb5f03b-75bb-4c2f-a658-0de489c5b017')
