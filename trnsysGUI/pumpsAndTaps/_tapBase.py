import typing as _tp

import dataclasses_jsonschema as _dcj

from trnsysGUI import createSinglePipePortItem as _cspi, internalPiping as _ip
from trnsysGUI.massFlowSolver import networkModel as _mfn
from trnsysGUI.pumpsAndTaps import (
    _pumpsAndTabsBase as _ptb,
    serialization as _ser,
)


class TapBase(_ptb.PumpsAndTabsBase):
    def __init__(
        self,
        trnsysType: str,
        editor,
        direction: _mfn.PortItemDirection,
        displayName: str,
    ) -> None:
        super().__init__(trnsysType, editor, displayName)

        self._modelTerminal: _mfn.TerminalWithPrescribedFlowBase

        if direction == _mfn.PortItemDirection.OUTPUT:
            self._graphicalPortItem = _cspi.createSinglePipePortItem("o", self)
            self.outputs.append(self._graphicalPortItem)
            modelPortItem = _mfn.PortItem("Out", _mfn.PortItemDirection.OUTPUT)
            self._modelTerminal = _mfn.TerminalWithPrescribedPosFlow(
                modelPortItem
            )
        elif direction == _mfn.PortItemDirection.INPUT:
            self._graphicalPortItem = _cspi.createSinglePipePortItem("i", self)
            self.inputs.append(self._graphicalPortItem)
            modelPortItem = _mfn.PortItem("In", _mfn.PortItemDirection.INPUT)
            self._modelTerminal = _mfn.TerminalWithPrescribedNegFlow(
                modelPortItem
            )
        else:
            raise AssertionError("Shouldn't get here.")

        self.changeSize()

    def getInternalPiping(self) -> _ip.InternalPiping:
        internalPiping = _ip.InternalPiping(
            [self._modelTerminal],
            {self._modelTerminal.portItem: self._graphicalPortItem},
        )

        return internalPiping

    def encode(self) -> _tp.Tuple[str, _dcj.JsonDict]:
        blockItemWithPrescribedMassFlowModel = (
            self._createBlockItemWithPrescribedMassFlowForEncode()
        )

        terminalModel = _ser.TerminalWithPrescribedMassFlowModel(
            self.name,
            self.displayName,
            blockItemWithPrescribedMassFlowModel,
            self._graphicalPortItem.id,
        )

        return "Block-", terminalModel.to_dict()

    def decode(self, i: _dcj.JsonDict, resBlockList) -> None:
        model = _ser.TerminalWithPrescribedMassFlowModel.from_dict(i)

        assert model.BlockName == self.name

        self.setDisplayName(model.BlockDisplayName)
        self._graphicalPortItem.id = model.portId
        self._applyBlockItemModelWithPrescribedMassFlowForDecode(
            model.blockItemWithPrescribedMassFlow
        )

        resBlockList.append(self)

    def changeSize(self) -> _tp.Tuple[int, int]:
        h, w = self._getCappedWidthAndHeight()

        rect = self.label.boundingRect()
        lw = rect.width()
        lx = (w - lw) / 2
        self.label.setPos(lx, h)

        delta = 20
        self._setUnFlippedPortPos(delta)

        self.updateFlipStateH(self.flippedH)
        self.updateFlipStateV(self.flippedV)

        return w, h

    def _setUnFlippedPortPos(self, delta: int) -> None:
        raise NotImplementedError()
