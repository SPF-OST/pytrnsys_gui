import dataclasses as _dc
import typing as _tp
import uuid as _uuid

import dataclasses_jsonschema as _dcj

import pytrnsys.utils.serialization as _ser
import trnsysGUI.BlockItem as _bi
import trnsysGUI.doublePipeModelPortItems as _dpmpi
import trnsysGUI.images as _img
import trnsysGUI.massFlowSolver as _mfs
import trnsysGUI.massFlowSolver.networkModel as _mfn


class DoublePipeConnectorBase(_bi.BlockItem, _mfs.MassFlowNetworkContributorMixin):
    def __init__(self, trnsysType, parent, **kwargs):
        super().__init__(trnsysType, parent, **kwargs)

        self.w = 40
        self.h = 20

        self.childIds = []
        self.childIds.append(self.trnsysId)
        self.childIds.append(self.parent.parent().idGen.getTrnsysID())

        self._updateModelPipes(self.displayName)

    def _getImageAccessor(self) -> _tp.Optional[_img.ImageAccessor]:
        raise NotImplementedError()

    def rotateBlockCW(self):
        super().rotateBlockCW()
        self._flipPipes()

    def rotateBlockCCW(self):
        super().rotateBlockCCW()
        self._flipPipes()

    def resetRotation(self):
        super().resetRotation()
        self.updateFlipStateV(0)

    def encode(self):
        portListInputs = []
        portListOutputs = []

        for inp in self.inputs:
            portListInputs.append(inp.id)
        for output in self.outputs:
            portListOutputs.append(output.id)

        blockPosition = (float(self.pos().x()), float(self.pos().y()))

        connectorModel = DoublePipeBlockItemModel(
            self.name,
            self.displayName,
            blockPosition,
            self.id,
            self.trnsysId,
            self.childIds,
            portListInputs,
            portListOutputs,
            self.flippedH,
            self.flippedV,
            self.rotationN,
        )

        dictName = "Block-"
        return dictName, connectorModel.to_dict()

    def decode(self, i, resBlockList):
        model = DoublePipeBlockItemModel.from_dict(i)

        self.setDisplayName(model.BlockDisplayName)
        self.setPos(float(model.blockPosition[0]), float(model.blockPosition[1]))
        self.id = model.id
        self.trnsysId = model.trnsysId
        self.childIds = model.childIds

        for index, inp in enumerate(self.inputs):
            inp.id = model.portsIdsIn[index]

        for index, out in enumerate(self.outputs):
            out.id = model.portsIdsOut[index]

        self.updateFlipStateH(model.flippedH)
        self.updateFlipStateV(model.flippedV)
        self.rotateBlockToN(model.rotationN)

        resBlockList.append(self)

    def getInternalPiping(self) -> _mfs.InternalPiping:
        raise NotImplementedError()

    def _updateModelPipes(self, displayName: str) -> None:
        coldInput = _dpmpi.ColdPortItem("coldInput", _mfn.PortItemType.INPUT)
        coldOutput = _dpmpi.ColdPortItem("coldOutput", _mfn.PortItemType.OUTPUT)
        self._coldPipe = _mfn.Pipe(displayName + "Cold", self.childIds[0], coldInput, coldOutput)

        hotInput = _dpmpi.HotPortItem("hotInput", _mfn.PortItemType.INPUT)
        hotOutput = _dpmpi.HotPortItem("hotOutput", _mfn.PortItemType.OUTPUT)
        self._hotPipe = _mfn.Pipe(displayName + "Hot", self.childIds[1], hotInput, hotOutput)

    def setDisplayName(self, newName):
        super().setDisplayName(newName)
        self._updateModelPipes(newName)

    def _flipPipes(self):
        angle = (self.rotationN % 4) * 90
        if angle == 0:
            self.updateFlipStateV(False)
        elif angle == 90:
            self.updateFlipStateV(True)
        elif angle == 180:
            self.updateFlipStateV(True)
        elif angle == 270:
            self.updateFlipStateV(False)


@_dc.dataclass
class DoublePipeBlockItemModel(_ser.UpgradableJsonSchemaMixinVersion0):  # pylint: disable=too-many-instance-attributes
    BlockName: str  # pylint: disable=invalid-name
    BlockDisplayName: str  # pylint: disable=invalid-name
    blockPosition: _tp.Tuple[float, float]
    id: int  # pylint: disable=invalid-name
    trnsysId: int
    childIds: _tp.List[int]
    portsIdsIn: _tp.List[int]
    portsIdsOut: _tp.List[int]
    flippedH: bool
    flippedV: bool
    rotationN: int

    @classmethod
    def from_dict(
        cls,
        data: _dcj.JsonDict,
        validate=True,  # pylint: disable=duplicate-code
        validate_enums: bool = True,
    ) -> "DoublePipeBlockItemModel":
        data.pop(".__BlockDict__")
        doublePipeBlockItemModel = super().from_dict(data, validate, validate_enums)
        return _tp.cast(DoublePipeBlockItemModel, doublePipeBlockItemModel)

    def to_dict(
        self,
        omit_none: bool = True,
        validate: bool = False,
        validate_enums: bool = True,
    ) -> _dcj.JsonDict:
        data = super().to_dict(omit_none, validate, validate_enums)  # pylint: disable=duplicate-code
        data[".__BlockDict__"] = True
        return data

    @classmethod
    def getVersion(cls) -> _uuid.UUID:
        return _uuid.UUID("e5149c30-9f05-4a3a-8a3c-9ada74143802")
