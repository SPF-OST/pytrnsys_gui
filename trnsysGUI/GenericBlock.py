# pylint: skip-file
# type: ignore

import pathlib as _pl
import typing as _tp

import PyQt5.QtWidgets as _qtw

import pytrnsys.utils.serialization as _ser
import trnsysGUI.blockItemGraphicItemMixins as _bmx
import trnsysGUI.blockItemHasInternalPiping as _biip
import trnsysGUI.createSinglePipePortItem as _cspi
import trnsysGUI.genericBlockModel as _gbm
import trnsysGUI.imageAccessor as _ia
import trnsysGUI.images as _img
import trnsysGUI.internalPiping as _ip
import trnsysGUI.massFlowSolver.networkModel as _mfn
import trnsysGUI.sideNrs as _snrs

_PORT_OFFSET = (
    8  # distance of the ports from the block border and from its corners
)


class GenericBlock(
    _biip.BlockItemHasInternalPiping, _bmx.RasterImageBlockItemMixin
):
    def __init__(self, trnsysType: str, editor, displayName: str) -> None:
        _biip.BlockItemHasInternalPiping.__init__(
            self, trnsysType, editor, displayName
        )
        _bmx.RasterImageBlockItemMixin.__init__(self)

        self.inputs.append(_cspi.createSinglePipePortItem("i", self))
        self.outputs.append(_cspi.createSinglePipePortItem("o", self))

        # Side of each port pair (same index as `inputs` and `outputs`), in the
        # coordinates of the block (i.e. before flipping and rotating)
        self.portPairSides: _tp.List[_snrs.SideNr] = [_snrs.SideNrs.RIGHT]

        # One trnsys ID per port pair (same index as `inputs` and `outputs`)
        self.childIds = []
        self.childIds.append(self.trnsysId)

        self._imageAccessor = _img.GENERIC_BLOCK_PNG

        # Disallow adding port pairs later, because the trnsysIDs of the generated port pairs have to be
        # consecutive to be correctly printed out in the export
        self.isSet = True

        self.changeSize()

    def getDisplayName(self) -> str:
        return self.displayName

    def _getImageAccessor(self) -> _tp.Optional[_ia.ImageAccessorBase]:
        return _img.GENERIC_BLOCK_PNG

    def changeSize(self):
        w = self.w
        h = self.h

        """ Resize block function """

        # Limit the block size:
        if h < 20:
            h = 20
        if w < 40:
            w = 40
        # center label:
        rect = self.label.boundingRect()
        lw, lh = rect.width(), rect.height()
        lx = (w - lw) / 2
        self.label.setPos(lx, h)

        self._layOutPortPairs()

        return w, h

    def _layOutPortPairs(self) -> None:
        """Distributes the ports of each side evenly along it, input before output."""
        for side in _tp.get_args(_snrs.SideNr):
            pairIndices = [
                i for i, s in enumerate(self.portPairSides) if s == side
            ]
            if not pairIndices:
                continue

            isVertical = side in (_snrs.SideNrs.LEFT, _snrs.SideNrs.RIGHT)
            length = self.h if isVertical else self.w
            nPorts = 2 * len(pairIndices)
            distBetweenPorts = (length - 2 * _PORT_OFFSET) / (nPorts - 1)

            ports = [
                port
                for i in pairIndices
                for port in (self.inputs[i], self.outputs[i])
            ]
            for portNr, port in enumerate(ports):
                along = _PORT_OFFSET + distBetweenPorts * portNr
                port.setPos(*self._getPortPosition(side, along))

    def _getPortPosition(
        self, side: _snrs.SideNr, along: float
    ) -> _tp.Tuple[float, float]:
        if side == _snrs.SideNrs.LEFT:
            return -_PORT_OFFSET, along
        if side == _snrs.SideNrs.RIGHT:
            return self.w + _PORT_OFFSET, along
        if side == _snrs.SideNrs.TOP:
            return along, -_PORT_OFFSET
        if side == _snrs.SideNrs.BOTTOM:
            return along, self.h + _PORT_OFFSET
        raise ValueError(f"Unknown side: {side}")

    def addPortDlg(self):
        self.editor.showGenericPortPairDlg(self)

    def addPort(self, io, relH):
        self.logger.debug(io)
        self.logger.debug(relH)

    def setImage(self):
        self._image = self._imageAccessor.image()

    def changeImage(self):
        name = str(self.pickImage().resolve())
        if name[-3:] == "png" or name[-3:] == "svg":
            self.setImageSource(name)
            self.setImage()
        else:
            self.logger.debug("No image picked, name is " + name)

    def setImageSource(self, name):
        self._imageAccessor = _ia.createForFile(_pl.Path(name))

    def pickImage(self):
        return _pl.Path(
            _qtw.QFileDialog.getOpenFileName(
                self.editor, filter="*.png *.svg"
            )[0]
        )

    def _addChildContextMenuActions(self, contextMenu: _qtw.QMenu) -> None:
        super()._addChildContextMenuActions(contextMenu)

        setImageAction = contextMenu.addAction("Set image")
        setImageAction.triggered.connect(self.changeImage)

        if not self.isSet:
            addPortAction = contextMenu.addAction("Add port")
            addPortAction.triggered.connect(self.addPortDlg)

    def encode(self):
        genericBlockModel = _gbm.GenericBlockModel(
            self.name,
            self.displayName,
            self._encodeBaseModel(),
            [i.id for i in self.inputs],
            [o.id for o in self.outputs],
            [*self.portPairSides],
            self._imageAccessor.getResourcePath(),
        )

        dictName = "Block-"
        return dictName, genericBlockModel.to_dict()

    def decode(self, i, resBlockList):
        try:
            model = _gbm.GenericBlockModel.from_dict(i)
        except _ser.SerializationError as error:
            # Generic blocks saved before `GenericBlockModel` could never be loaded, so their
            # format isn't supported
            displayName = i.get("BlockDisplayName")
            raise _ser.SerializationError(
                f"Generic block '{displayName}' was saved in a format that is no longer supported. "
                "Remove it and its connections from the diagram file, or recreate it."
            ) from error

        self.setDisplayName(model.BlockDisplayName)

        self._removePortPairs()
        for side in model.portPairSides:
            self.addPortPair(side)

        for port, portId in zip(self.inputs, model.portsIdsIn):
            port.id = portId
        for port, portId in zip(self.outputs, model.portsIdsOut):
            port.id = portId

        self._imageAccessor = _ia.createFromResourcePath(
            model.imageResourcePath
        )
        self.setImage()

        self._decodeBaseModel(model.blockItemModel)
        self.childIds[0] = self.trnsysId

        resBlockList.append(self)

    def _removePortPairs(self):
        assert len(self.inputs) == len(self.outputs)
        numberOfPortPairs = len(self.inputs)
        for _ in range(numberOfPortPairs):
            self.removePortPair(0)

    def addPortPair(self, side: _snrs.SideNr) -> None:
        self.logger.debug("side is " + str(side))
        self.inputs.append(_cspi.createSinglePipePortItem("i", self))
        self.outputs.append(_cspi.createSinglePipePortItem("o", self))
        self.portPairSides.append(side)
        # Allocate id
        self.childIds.append(self.editor.idGen.getTrnsysID())

        self._layOutPortPairs()

    def removePortPair(self, n: int) -> None:
        for port in (self.inputs.pop(n), self.outputs.pop(n)):
            scene = port.scene()
            if scene:
                scene.removeItem(port)
            else:
                port.setParentItem(None)
        del self.portPairSides[n]
        del self.childIds[n]

        self._layOutPortPairs()

    def getInternalPiping(self) -> _ip.InternalPiping:
        assert len(self.inputs) == len(self.outputs)

        pipes = []
        portItems = {}
        for i, (graphicalInputPort, graphicalOutputPort) in enumerate(
            zip(self.inputs, self.outputs)
        ):
            inputPort = _mfn.PortItem("In", _mfn.PortItemDirection.INPUT)
            outputPort = _mfn.PortItem("Out", _mfn.PortItemDirection.OUTPUT)
            pipe = _mfn.Pipe(inputPort, outputPort, name=f"Side{i}")

            pipes.append(pipe)
            portItems[inputPort] = graphicalInputPort
            portItems[outputPort] = graphicalOutputPort

        return _ip.InternalPiping(pipes, portItems)
