# pylint: disable = invalid-name

import dataclasses as _dc
import typing as _tp
import uuid as _uuid

import dataclasses_jsonschema as _dcj
from PyQt5.QtWidgets import QGraphicsTextItem

import pytrnsys.utils.serialization as _ser
import trnsysGUI.blockItemModel as _bim
import trnsysGUI.createSinglePipePortItem as _cspi  # pylint: disable=cyclic-import
import trnsysGUI.images as _img
import trnsysGUI.massFlowSolver as _mfs
import trnsysGUI.massFlowSolver.networkModel as _mfn
from trnsysGUI.BlockItem import BlockItem
from trnsysGUI.massFlowSolver import MassFlowNetworkContributorMixin


class TVentil(BlockItem, MassFlowNetworkContributorMixin):  # pylint: disable = too-many-instance-attributes
    def __init__(self, trnsysType, parent, **kwargs):
        super().__init__(trnsysType, parent, **kwargs)

        self.h = 40
        self.w = 40
        self.isTempering = False
        self.positionForMassFlowSolver = 1.0
        self.posLabel = QGraphicsTextItem(str(self.positionForMassFlowSolver), self)
        self.posLabel.setVisible(False)

        self.outputs.append(_cspi.createSinglePipePortItem("o", 2, self))
        self.outputs.append(_cspi.createSinglePipePortItem("o", 2, self))
        self.inputs.append(_cspi.createSinglePipePortItem("i", 0, self))

        self.changeSize()

    def _getImageAccessor(self) -> _tp.Optional[_img.ImageAccessor]:
        return _img.T_VENTIL_SVG

    def changeSize(self):
        width = self.w
        height = self.h

        delta = 20
        # Limit the block size:
        height = max(height, 20)
        width = max(width, 40)

        # center label:
        rect = self.label.boundingRect()
        labelWidth = rect.width()
        labelPosX = (width - labelWidth) / 2

        self.label.setPos(labelPosX, height - self.flippedV * (height + height / 2))
        self.posLabel.setPos(labelPosX + 5, -15)

        self.origInputsPos = [[width, delta]]
        self.origOutputsPos = [[0, delta], [delta, 0]]

        self.inputs[0].setPos(self.origInputsPos[0][0], self.origInputsPos[0][1])
        self.outputs[0].setPos(self.origOutputsPos[0][0], self.origOutputsPos[0][1])
        self.outputs[1].setPos(self.origOutputsPos[1][0], self.origOutputsPos[1][1])

        self.updateFlipStateH(self.flippedH)
        self.updateFlipStateV(self.flippedV)

        self.inputs[0].side = (self.rotationN + 2 - 2 * self.flippedH) % 4
        self.outputs[0].side = (self.rotationN + 2 * self.flippedH) % 4
        self.outputs[1].side = (self.rotationN + 1 + 2 * self.flippedV) % 4

        return width, height

    def rotateBlockCW(self):
        super().rotateBlockCW()
        # Rotate valve position label back so it will always stay horizontal
        self._updateRotation()

    def rotateBlockCCW(self):
        super().rotateBlockCCW()
        # Rotate valve position label back so it will always stay horizontal
        self._updateRotation()

    def resetRotation(self):
        super().resetRotation()
        # Rotate valve position label back so it will always stay horizontal
        self._updateRotation()

    def _updateRotation(self):
        self.posLabel.setRotation(-self.rotationN * 90)

    def setComplexDiv(self, b):  # pylint: disable = invalid-name
        self.isTempering = bool(b)

    def setPositionForMassFlowSolver(self, f):  # pylint: disable = invalid-name
        self.positionForMassFlowSolver = f

    def encode(self):
        portListInputs = []
        portListOutputs = []

        for inp in self.inputs:
            portListInputs.append(inp.id)
        for output in self.outputs:
            portListOutputs.append(output.id)

        blockPosition = (float(self.pos().x()), float(self.pos().y()))

        tVentilModel = TVentilModel(
            self.name,
            self.displayName,
            blockPosition,
            self.id,
            self.trnsysId,
            portListInputs,  # pylint: disable = duplicate-code # 2
            portListOutputs,
            self.flippedH,
            self.flippedV,
            self.rotationN,
        )

        dictName = "Block-"

        dct = tVentilModel.to_dict()

        dct["IsTempering"] = self.isTempering
        dct["PositionForMassFlowSolver"] = self.positionForMassFlowSolver
        return dictName, dct

    def decode(self, i, resBlockList):
        model = TVentilModel.from_dict(i)

        self.setDisplayName(model.BlockDisplayName)
        self.setPos(float(model.blockPosition[0]), float(model.blockPosition[1]))
        self.id = model.Id
        self.trnsysId = model.trnsysId

        self.inputs[0].id = model.portsIdsIn[0]
        self.outputs[0].id = model.portsIdsOut[0]
        self.outputs[1].id = model.portsIdsOut[1]

        self.updateFlipStateH(model.flippedH)
        self.updateFlipStateV(model.flippedV)
        self.rotateBlockToN(model.rotationN)

        resBlockList.append(self)

        if "IsTempering" not in i or "PositionForMassFlowSolver" not in i:
            self.logger.debug("Old version of diagram")
            self.positionForMassFlowSolver = 1.0
        else:
            self.isTempering = i["IsTempering"]
            self.positionForMassFlowSolver = i["PositionForMassFlowSolver"]

    def decodePaste(self, i, offset_x, offset_y, resConnList, resBlockList, **kwargs):
        super().decodePaste(i, offset_x, offset_y, resConnList, resBlockList, **kwargs)
        if "IsTempering" not in i or "PositionForMassFlowSolver" not in i:
            self.logger.debug("Old version of diagram")
            self.positionForMassFlowSolver = 1.0
        else:
            self.isTempering = i["IsTempering"]
            self.positionForMassFlowSolver = i["PositionForMassFlowSolver"]

    def exportMassFlows(self):
        if not self.isTempering:
            resStr = "xFrac" + self.displayName + " = " + str(self.positionForMassFlowSolver) + "\n"
            equationNr = 1
            return resStr, equationNr
        return "", 0

    def exportDivSetting1(self):
        if self.isTempering:
            constants = 1
            line = "T_set_" + self.displayName + "=50\n"
            return line, constants
        return "", 0

    def exportDivSetting2(self, nUnit):
        if self.isTempering:
            lines = ""
            nUnit = nUnit + 1
            lines += f"UNIT {nUnit} TYPE 811 ! Passive Divider for heating \n"
            lines += "PARAMETERS 1" + "\n"
            lines += "5 !Nb.of iterations before fixing the value \n"
            lines += "INPUTS 4 \n"

            if (
                    self.outputs[0].pos().y() == self.inputs[0].pos().y()
                    or self.outputs[0].pos().x() == self.inputs[0].pos().x()
            ):
                first = self.outputs[0]
                second = self.outputs[1]

            lines += "T" + first.connectionList[0].displayName + "\n"
            lines += "T" + second.connectionList[0].displayName + "\n"
            lines += "Mfr" + self.inputs[0].connectionList[0].displayName + "\n"

            lines += "T_set_" + self.displayName + "\n"
            lines += "*** INITIAL INPUT VALUES" + "\n"
            lines += "35.0 21.0 800.0 T_set_" + self.displayName + "\n"

            lines += "EQUATIONS 1\n"
            lines += f"xFrac{self.displayName} =  1.-[{nUnit},5] \n\n"

            return lines, nUnit
        return "", nUnit

    def getInternalPiping(self) -> _mfs.InternalPiping:
        teePiece, modelPortItemsToGraphicalPortItem = self._getModelAndMapping()

        return _mfs.InternalPiping([teePiece], modelPortItemsToGraphicalPortItem)

    def _getModelAndMapping(self):
        inputPort = _mfn.PortItem("input", _mfn.PortItemType.INPUT)
        output1 = _mfn.PortItem("straightOutput", _mfn.PortItemType.OUTPUT)
        output2 = _mfn.PortItem("orthogonalOutput", _mfn.PortItemType.OUTPUT)
        teePiece = _mfn.Diverter(self.displayName, self.trnsysId, inputPort, output1, output2)
        modelPortItemsToGraphicalPortItem = {inputPort: self.inputs[0], output1: self.outputs[0],
                                             output2: self.outputs[1]}
        return teePiece, modelPortItemsToGraphicalPortItem

    def exportPipeAndTeeTypesForTemp(self, startingUnit):
        if self.isVisible():
            lines = ""
            unitNumber = startingUnit
            tNr = 929  # Temperature calculation from a tee-piece

            unitText = ""
            ambientT = 20

            equationConstant = 1

            unitText += "UNIT " + str(unitNumber) + " TYPE " + str(tNr) + "\n"
            unitText += "!" + self.displayName + "\n"
            unitText += "PARAMETERS 0\n"
            unitText += "INPUTS 6\n"

            openLoops, _ = self._getOpenLoopsAndNodeToIndices()
            assert len(openLoops) == 1
            openLoop = openLoops[0]

            assert len(openLoop.realNodes) == 1
            realNode = openLoop.realNodes[0]

            outputVariables = realNode.getOutputVariables()
            for outputVariable in outputVariables:
                if not outputVariable:
                    continue

                unitText += outputVariable.name + "\n"

            unitText += f"T{self.inputs[0].connectionList[0].displayName}\n"
            unitText += f"T{self.outputs[0].connectionList[0].displayName}\n"
            unitText += f"T{self.outputs[1].connectionList[0].displayName}\n"

            unitText += "***Initial values\n"
            unitText += 3 * "0 " + 3 * (str(ambientT) + " ") + "\n"

            unitText += "EQUATIONS 1\n"
            unitText += "T" + self.displayName + "= [" + str(unitNumber) + "," + str(equationConstant) + "]\n"

            unitNumber += 1
            lines += unitText + "\n"

            return lines, unitNumber
        return "", startingUnit


@_dc.dataclass
class TVentilModel(_ser.UpgradableJsonSchemaMixin):  # pylint: disable=too-many-instance-attributes
    BlockName: str  # pylint: disable = invalid-name
    BlockDisplayName: str  # pylint: disable = invalid-name
    blockPosition: _tp.Tuple[float, float]
    Id: int  # pylint: disable = invalid-name
    trnsysId: int
    portsIdsIn: _tp.List[int]
    portsIdsOut: _tp.List[int]
    flippedH: bool
    flippedV: bool
    rotationN: int

    @classmethod
    def from_dict(
            cls,  # pylint: disable = duplicate-code
            data: _dcj.JsonDict,  # pylint: disable = duplicate-code
            validate=True,
            validate_enums: bool = True,
    ) -> "TVentilModel":
        tVentilModel = super().from_dict(data, validate, validate_enums)
        return _tp.cast(TVentilModel, tVentilModel)

    def to_dict(
            self,
            omit_none: bool = True,
            validate: bool = False,
            validate_enums: bool = True,  # pylint: disable=duplicate-code
    ) -> _dcj.JsonDict:  # pylint: disable = duplicate-code
        data = super().to_dict(omit_none, validate, validate_enums)
        data[".__BlockDict__"] = True
        return data

    @classmethod
    def getSupersededClass(cls) -> _tp.Type[_ser.UpgradableJsonSchemaMixin]:
        return _bim.BlockItemModel

    @classmethod
    def upgrade(cls, superseded: _bim.BlockItemModel) -> "TVentilModel":  # type: ignore[override]
        assert len(superseded.portsIdsIn) == 2
        assert len(superseded.portsIdsOut) == 1

        inputPortIds = [superseded.portsIdsOut[0]]
        outputPortIds = [superseded.portsIdsIn[0], superseded.portsIdsIn[1]]

        return TVentilModel(
            superseded.BlockName,
            superseded.BlockDisplayName,
            superseded.blockPosition,
            superseded.Id,
            superseded.trnsysId,
            inputPortIds,
            outputPortIds,
            superseded.flippedH,
            superseded.flippedV,
            superseded.rotationN,
        )

    @classmethod
    def getVersion(cls) -> _uuid.UUID:
        return _uuid.UUID('3fff9a8a-d40e-42e2-824d-c015116d0a1d')
