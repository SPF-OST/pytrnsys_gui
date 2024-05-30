# pylint: disable = invalid-name

import typing as _tp

import PyQt5.QtWidgets as _qtw
import dataclasses_jsonschema as _dcj

import trnsysGUI.connection.names as _cnames
import trnsysGUI.createSinglePipePortItem as _cspi  # pylint: disable=cyclic-import
import trnsysGUI.images as _img
import trnsysGUI.internalPiping as _ip
import trnsysGUI.massFlowSolver.names as _mnames
import trnsysGUI.massFlowSolver.networkModel as _mfn
import trnsysGUI.svgBlockItem as _svgbi
import trnsysGUI.temperatures as _temps
import trnsysGUI.valveModel as _vm


class TVentil(_svgbi.SvgBlockItem):  # pylint: disable = too-many-instance-attributes
    def __init__(self, trnsysType: str, editor, displayName: str) -> None:
        super().__init__(trnsysType, editor, displayName)

        self.h = 40
        self.w = 40
        self.isTempering = False
        self.positionForMassFlowSolver = 1.0
        self.posLabel = _qtw.QGraphicsTextItem(str(self.positionForMassFlowSolver), self)
        self.posLabel.setVisible(False)

        self.outputs.append(_cspi.createSinglePipePortItem("o", 2, self))
        self.outputs.append(_cspi.createSinglePipePortItem("o", 2, self))
        self.inputs.append(_cspi.createSinglePipePortItem("i", 0, self))

        inputPort = _mfn.PortItem("In", _mfn.PortItemDirection.INPUT)
        output1 = _mfn.PortItem("StrOut", _mfn.PortItemDirection.OUTPUT)
        output2 = _mfn.PortItem("OrtOut", _mfn.PortItemDirection.OUTPUT)
        self.modelDiverter = _mfn.Diverter(inputPort, output1, output2)

        self.changeSize()

    def getDisplayName(self) -> str:
        return self.displayName

    @classmethod
    @_tp.override
    def hasDdckPlaceHolders(cls) -> bool:
        return False

    @classmethod
    @_tp.override
    def shallRenameOutputTemperaturesInHydraulicFile(cls) -> bool:
        return False

    def _getImageAccessor(self) -> _img.SvgImageAccessor:
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

    def encode(self) -> _tp.Tuple[str, _dcj.JsonDict]:
        portListInputs = []
        portListOutputs = []

        for inp in self.inputs:
            portListInputs.append(inp.id)
        for output in self.outputs:
            portListOutputs.append(output.id)

        blockItemModel = self._encodeBaseModel()

        inputPortId = self.inputs[0].id
        outputPortIds = (self.outputs[0].id, self.outputs[1].id)

        valveModel = _vm.ValveModel(self.name, self.displayName, blockItemModel, inputPortId, outputPortIds)

        dictName = "Block-"

        dct = valveModel.to_dict()

        dct["IsTempering"] = self.isTempering
        dct["PositionForMassFlowSolver"] = self.positionForMassFlowSolver
        return dictName, dct

    def decode(self, i, resBlockList) -> None:
        model = _vm.ValveModel.from_dict(i)

        self.setDisplayName(model.BlockDisplayName)

        self.inputs[0].id = model.inputPortId
        self.outputs[0].id = model.outputPortIds[0]
        self.outputs[1].id = model.outputPortIds[1]

        self._decodeBaseModel(model.blockItemModel)

        resBlockList.append(self)

        if "IsTempering" not in i or "PositionForMassFlowSolver" not in i:
            self.logger.debug("Old version of diagram")
            self.positionForMassFlowSolver = 1.0
        else:
            self.isTempering = i["IsTempering"]
            self.positionForMassFlowSolver = i["PositionForMassFlowSolver"]

    def exportMassFlows(self):
        if not self.isTempering:
            mfsInputVariableName = _mnames.getInputVariableName(self, self.modelDiverter)
            resStr = f"{mfsInputVariableName} = {self.positionForMassFlowSolver}\n"
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
            lines += "M" + self.inputs[0].connectionList[0].displayName + "\n"

            lines += "T_set_" + self.displayName + "\n"
            lines += "*** INITIAL INPUT VALUES" + "\n"
            lines += "35.0 21.0 800.0 T_set_" + self.displayName + "\n"

            mfsInputVariableName = _mnames.getInputVariableName(self, self.modelDiverter)
            lines += "EQUATIONS 1\n"
            lines += f"{mfsInputVariableName} =  1.-[{nUnit},5] \n\n"

            return lines, nUnit
        return "", nUnit

    def getInternalPiping(self) -> _ip.InternalPiping:
        modelPortItemsToGraphicalPortItem = {
            self.modelDiverter.input: self.inputs[0],
            self.modelDiverter.output1: self.outputs[0],
            self.modelDiverter.output2: self.outputs[1],
        }

        return _ip.InternalPiping([self.modelDiverter], modelPortItemsToGraphicalPortItem)

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

            portItems = self.modelDiverter.getPortItems()
            massFlowVariableNames = [
                _mnames.getMassFlowVariableName(self.displayName, self.modelDiverter, portItems[0]),
                _mnames.getMassFlowVariableName(self.displayName, self.modelDiverter, portItems[1]),
                _mnames.getMassFlowVariableName(self.displayName, self.modelDiverter, portItems[2]),
            ]

            unitText += "\n".join(massFlowVariableNames) + "\n"

            temperatureVariableNames = [
                _cnames.getTemperatureVariableName(self.inputs[0].getConnection(), _mfn.PortItemType.STANDARD),
                _cnames.getTemperatureVariableName(self.outputs[0].getConnection(), _mfn.PortItemType.STANDARD),
                _cnames.getTemperatureVariableName(self.outputs[1].getConnection(), _mfn.PortItemType.STANDARD),
            ]

            unitText += "\n".join(temperatureVariableNames) + "\n"

            unitText += "***Initial values\n"
            unitText += 3 * "0 " + 3 * (str(ambientT) + " ") + "\n"

            unitText += "EQUATIONS 1\n"
            temperatureVariableName = _temps.getInternalTemperatureVariableName(
                componentDisplayName=self.displayName, nodeName=self.modelDiverter.name
            )
            unitText += f"{temperatureVariableName}= [{unitNumber},{equationConstant}]\n"

            unitNumber += 1
            lines += unitText + "\n"

            return lines, unitNumber
        return "", startingUnit
