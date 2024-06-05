# pylint: disable = invalid-name
import typing as _tp

import trnsysGUI.blockItemGraphicItemMixins as _gimx
import trnsysGUI.blockItemHasInternalPiping as _bip
import trnsysGUI.createSinglePipePortItem as _cspi
import trnsysGUI.images as _img
import trnsysGUI.internalPiping as _ip


class BlockItemFourPorts(
    _bip.BlockItemHasInternalPiping, _gimx.SvgBlockItemGraphicItemMixin
):  # pylint: disable = too-many-instance-attributes
    def __init__(self, trnsysType: str, editor, displayName: str) -> None:
        super().__init__(trnsysType, editor, displayName)

        self.logger = editor.logger

        self.h = 120
        self.w = 120
        self.inputs.append(_cspi.createSinglePipePortItem("i", 0, self))
        self.inputs.append(_cspi.createSinglePipePortItem("i", 2, self))
        self.outputs.append(_cspi.createSinglePipePortItem("o", 0, self))
        self.outputs.append(_cspi.createSinglePipePortItem("o", 2, self))

        self.childIds = []
        self.childIds.append(self.trnsysId)
        self.childIds.append(self.editor.idGen.getTrnsysID())

        self.changeSize()

    @classmethod
    @_tp.override
    def _getImageAccessor(cls) -> _img.SvgImageAccessor:  # pylint: disable=arguments-differ
        raise NotImplementedError()

    def getDisplayName(self) -> str:
        return self.displayName

    def getInternalPiping(self) -> _ip.InternalPiping:
        raise NotImplementedError()

    def encode(self):
        if not self.isVisible():
            return None
        self.logger.debug(f"Encoding a {self.name} block")

        portListInputs = []
        portListOutputs = []

        for inputPort in self.inputs:
            portListInputs.append(inputPort.id)
        for outputPort in self.outputs:
            portListOutputs.append(outputPort.id)

        dct = {}
        dct[".__BlockDict__"] = True
        dct["BlockName"] = self.name
        dct["BlockDisplayName"] = self.displayName
        dct["PortsIDIn"] = portListInputs
        dct["PortsIDOut"] = portListOutputs
        dct[self.name + "Position"] = (float(self.pos().x()), float(self.pos().y()))
        dct["trnsysID"] = self.trnsysId
        dct["childIds"] = self.childIds
        dct["FlippedH"] = self.flippedH
        dct["FlippedV"] = self.flippedV
        dct["RotationN"] = self.rotationN

        dictName = "Block-"

        return dictName, dct

    def decode(self, i, resBlockList):
        self.updateFlipStateH(i["FlippedH"])
        self.updateFlipStateV(i["FlippedV"])
        self.rotateBlockToN(i["RotationN"])
        self.childIds = i["childIds"]
        self.displayName = i["BlockDisplayName"]
        self.changeSize()

        for x, inputPort in enumerate(self.inputs):
            inputPort.id = i["PortsIDIn"][x]

        for x, outputPort in enumerate(self.outputs):
            outputPort.id = i["PortsIDOut"][x]

        self.setPos(float(i[self.name + "Position"][0]), float(i[self.name + "Position"][1]))
        self.trnsysId = i["trnsysID"]

        resBlockList.append(self)

    def getSubBlockOffset(self, c):  # pylint: disable = invalid-name
        for i in range(2):
            if (
                self.inputs[i] == c.toPort
                or self.inputs[i] == c.fromPort
                or self.outputs[i] == c.toPort
                or self.outputs[i] == c.fromPort
            ):
                return i
        return None
