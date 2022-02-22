# pylint: skip-file
# type: ignore

import dataclasses as _dc
import typing as _tp
import uuid as _uuid

import dataclasses_jsonschema as _dcj
from PyQt5.QtWidgets import QGraphicsTextItem

import trnsysGUI.blockItemModel as _bim
import trnsysGUI.createSinglePipePortItem as _cspi
import trnsysGUI.images as _img
import trnsysGUI.massFlowSolver as _mfs
import trnsysGUI.massFlowSolver.networkModel as _mfn
import pytrnsys.utils.serialization as _ser
from trnsysGUI.BlockItem import BlockItem
from trnsysGUI.massFlowSolver import MassFlowNetworkContributorMixin


class TVentil(BlockItem, MassFlowNetworkContributorMixin):
    def __init__(self, trnsysType, parent, **kwargs):
        super(TVentil, self).__init__(trnsysType, parent, **kwargs)

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
        w = self.w
        h = self.h

        delta = 20
        # Limit the block size:
        if h < 20:
            h = 20
        if w < 40:
            w = 40

        # center label:
        rect = self.label.boundingRect()
        lw, lh = rect.width(), rect.height()
        lx = (w - lw) / 2

        self.label.setPos(lx, h - self.flippedV * (h + h / 2))
        self.posLabel.setPos(lx + 5, -15)

        self.origInputsPos = [[w, delta]]
        self.origOutputsPos = [[0, delta], [delta, 0]]

        self.inputs[0].setPos(self.origInputsPos[0][0], self.origInputsPos[0][1])
        self.outputs[0].setPos(self.origOutputsPos[0][0], self.origOutputsPos[0][1])
        self.outputs[1].setPos(self.origOutputsPos[1][0], self.origOutputsPos[1][1])

        self.updateFlipStateH(self.flippedH)
        self.updateFlipStateV(self.flippedV)

        self.inputs[0].side = (self.rotationN + 2 - 2 * self.flippedH) % 4
        self.outputs[0].side = (self.rotationN + 2 * self.flippedH) % 4
        self.outputs[1].side = (self.rotationN + 1 + 2 * self.flippedV) % 4

        return w, h

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

    def setComplexDiv(self, b):
        self.isTempering = bool(b)

    def setPositionForMassFlowSolver(self, f):
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
            portListInputs,
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

        self.setName(model.BlockDisplayName)
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
        super(TVentil, self).decodePaste(i, offset_x, offset_y, resConnList, resBlockList, **kwargs)
        if "IsTempering" or "PositionForMassFlowSolver" not in i:
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
        else:
            return "", 0

    def exportDivSetting1(self):
        if self.isTempering:
            constants = 1
            f = "T_set_" + self.displayName + "=50\n"
            return f, constants
        else:
            return "", 0

    def exportDivSetting2(self, nUnit):
        if self.isTempering:
            f = ""
            nUnit = nUnit + 1
            f += "UNIT %d TYPE 811 ! Passive Divider for heating \n" % nUnit
            f += "PARAMETERS 1" + "\n"
            f += "5 !Nb.of iterations before fixing the value \n"
            f += "INPUTS 4 \n"

            if (
                self.outputs[0].pos().y() == self.inputs[0].pos().y()
                or self.outputs[0].pos().x() == self.inputs[0].pos().x()
            ):
                first = self.inputs[0]
                second = self.inputs[1]

            f += "T" + first.connectionList[0].displayName + "\n"
            f += "T" + second.connectionList[0].displayName + "\n"
            f += "Mfr" + self.outputs[0].connectionList[0].displayName + "\n"

            f += "T_set_" + self.displayName + "\n"
            f += "*** INITIAL INPUT VALUES" + "\n"
            f += "35.0 21.0 800.0 T_set_" + self.displayName + "\n"

            f += "EQUATIONS 1\n"
            f += "xFrac" + self.displayName + " =  1.-[%d,5] \n\n" % nUnit

            return f, nUnit
        else:
            return "", nUnit

    def getInternalPiping(self) -> _mfs.InternalPiping:
        teePiece, modelPortItemsToGraphicalPortItem = self._getModelAndMapping()

        return _mfs.InternalPiping([teePiece], modelPortItemsToGraphicalPortItem)

    def _getModelAndMapping(self):
        input = _mfn.PortItem("input", _mfn.PortItemType.INPUT)
        output1 = _mfn.PortItem("straightOutput", _mfn.PortItemType.OUTPUT)
        output2 = _mfn.PortItem("orthogonalOutput", _mfn.PortItemType.OUTPUT)
        teePiece = _mfn.Diverter(self.displayName, self.trnsysId, input, output1, output2)
        modelPortItemsToGraphicalPortItem = {input: self.inputs[0], output1: self.outputs[0], output2: self.outputs[1]}
        return teePiece, modelPortItemsToGraphicalPortItem

    def exportPipeAndTeeTypesForTemp(self, startingUnit):
        if self.isVisible():
            f = ""
            unitNumber = startingUnit
            tNr = 929  # Temperature calculation from a tee-piece

            unitText = ""
            ambientT = 20

            equationConstant = 1

            unitText += "UNIT " + str(unitNumber) + " TYPE " + str(tNr) + "\n"
            unitText += "!" + self.displayName + "\n"
            unitText += "PARAMETERS 0\n"
            unitText += "INPUTS 6\n"

            openLoops, nodesToIndices = self._getOpenLoopsAndNodeToIndices()
            assert len(openLoops) == 1
            openLoop = openLoops[0]

            assert len(openLoop.realNodes) == 1
            realNode = openLoop.realNodes[0]

            outputVariables = realNode.serialize(nodesToIndices).outputVariables
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
            f += unitText + "\n"

            return f, unitNumber
        else:
            return "", startingUnit


@_dc.dataclass
class TVentilModel(_ser.UpgradableJsonSchemaMixin):  # pylint: disable=too-many-instance-attributes
    BlockName: str
    BlockDisplayName: str
    blockPosition: _tp.Tuple[float, float]
    Id: int
    trnsysId: int
    portsIdsIn: _tp.List[int]
    portsIdsOut: _tp.List[int]
    flippedH: bool
    flippedV: bool
    rotationN: int

    @classmethod
    def from_dict(
        cls,
        data: _dcj.JsonDict,
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
    ) -> _dcj.JsonDict:
        data = super().to_dict(omit_none, validate, validate_enums)
        data[".__BlockDict__"] = True
        return data

    @classmethod
    def getSupersededClass(cls) -> _tp.Type[_ser.UpgradableJsonSchemaMixin]:
        return _bim.BlockItemModel

    @classmethod
    def upgrade(cls, superseded: _bim.BlockItemModel) -> "TVentilModel": # type: ignore[override]
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
