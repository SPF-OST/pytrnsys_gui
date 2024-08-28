# pylint: skip-file
# type: ignore

import pathlib as _pl
import typing as _tp

import PyQt5.QtWidgets as _qtw

import trnsysGUI.blockItemGraphicItemMixins as _bmx
import trnsysGUI.blockItemHasInternalPiping as _biip
import trnsysGUI.createSinglePipePortItem as _cspi
import trnsysGUI.imageAccessor as _ia
import trnsysGUI.images as _img
import trnsysGUI.internalPiping as _ip
import trnsysGUI.massFlowSolver.networkModel as _mfn


class GenericBlock(_biip.BlockItemHasInternalPiping, _bmx.RasterImageBlockItemMixin):
    def __init__(self, trnsysType: str, editor, displayName: str) -> None:
        _biip.BlockItemHasInternalPiping.__init__(self, trnsysType, editor, displayName)
        _bmx.RasterImageBlockItemMixin.__init__(self)

        self.inputs.append(_cspi.createSinglePipePortItem("i", self))
        self.outputs.append(_cspi.createSinglePipePortItem("o", self))

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
        delta = 4

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

        self.outputs[0].setPos(2 * delta + w, h - 2 * delta)
        self.inputs[0].setPos(2 * delta + w, 2 * delta)

        return w, h

    def getPairNb(self, side):
        res = 0
        for i in self.inputs:
            if i.side == side:
                res += 1

        self.logger.debug("there are " + str(res) + " pairs on the side " + str(side))
        return res

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
        return _pl.Path(_qtw.QFileDialog.getOpenFileName(self.editor, filter="*.png *.svg")[0])

    def _addChildContextMenuActions(self, contextMenu: _qtw.QMenu) -> None:
        super()._addChildContextMenuActions(contextMenu)

        setImageAction = contextMenu.addAction("Set image")
        setImageAction.triggered.connect(self.changeImage)

        if not self.isSet:
            addPortAction = contextMenu.addAction("Add port")
            addPortAction.triggered.connect(self.addPortDlg)

    def encode(self):
        _, dct = super().encode()

        dct["PortPairsNb"] = [self.getPairNb(i) for i in range(4)]
        dct["Imagesource"] = self._imageAccessor.getResourcePath()

        dictName = "Block-"
        return dictName, dct

    def decode(self, i, resBlockList):
        self._removePortPairs()

        numberOfPortPairsBySide = i["PortPairsNb"]
        self._addPortPairs(numberOfPortPairsBySide)

        self._imageAccessor = _ia.createFromResourcePath(i["Imagesource"])
        self.setImage()

        super().decode(i, resBlockList)

    def _addPortPairs(self, numberOfPortPairsBySide):
        for side in range(3):
            numberOfPortPairsToAdd = numberOfPortPairsBySide[side]
            for _ in range(numberOfPortPairsToAdd):
                self.addPortPair(side)

    def _removePortPairs(self):
        assert len(self.inputs) == len(self.outputs)
        numberOfPortPairs = len(self.inputs)
        for portPairIndex in range(numberOfPortPairs):
            self.removePortPair(portPairIndex)

    def addPortPair(self, side):
        h = self.h
        w = self.w
        delta = 4
        self.logger.debug("side is " + str(side))
        self.inputs.append(_cspi.createSinglePipePortItem("i", self))
        self.outputs.append(_cspi.createSinglePipePortItem("o", self))
        # Allocate id
        self.childIds.append(self.editor.idGen.getTrnsysID())

        portNb = [0, 0, 0, 0]
        for i in self.inputs:
            if i.side == 0:
                distBetweenPorts = (self.h - 4 * delta) / (2 * self.getPairNb(0) - 1)
                self.logger.debug("distance betw ports " + str(distBetweenPorts))
                i.setPos(-2 * delta, 2 * delta + distBetweenPorts * portNb[0])
                portNb[0] += 1

                self.outputs[self.inputs.index(i)].setPos(-2 * delta, 2 * delta + distBetweenPorts * portNb[0])
                portNb[0] += 1
            elif i.side == 1:
                distBetweenPorts = (self.w - 4 * delta) / (2 * self.getPairNb(1) - 1)
                i.setPos(2 * delta + distBetweenPorts * portNb[1], -2 * delta)
                portNb[1] += 1

                self.outputs[self.inputs.index(i)].setPos(2 * delta + distBetweenPorts * portNb[1], -2 * delta)
                portNb[1] += 1

            elif i.side == 2:
                self.logger.debug("side == 2")
                distBetweenPorts = (self.h - 4 * delta) / (2 * self.getPairNb(2) - 1)
                self.logger.debug("side 2 dist betw ports is " + str(distBetweenPorts))
                i.setPos(2 * delta + w, 2 * delta + distBetweenPorts * portNb[2])
                self.logger.debug(2 * delta + distBetweenPorts * portNb[2])
                portNb[2] += 1

                self.outputs[self.inputs.index(i)].setPos(2 * delta + w, 2 * delta + distBetweenPorts * portNb[2])
                self.logger.debug(2 * delta + distBetweenPorts * portNb[2])
                portNb[2] += 1

            else:
                distBetweenPorts = (self.w - 4 * delta) / (2 * self.getPairNb(3) - 1)
                self.logger.debug("distance betw ports " + str(distBetweenPorts))
                i.setPos(2 * delta + distBetweenPorts * portNb[3], 2 * delta + h)
                portNb[3] += 1

                self.outputs[self.inputs.index(i)].setPos(2 * delta + distBetweenPorts * portNb[3], 2 * delta + h)
                portNb[3] += 1

    def removePortPairOnSide(self, side):
        for i in self.inputs:
            if i.side == side:
                self.removePortPair(self.inputs.index(i))
                return

    def removePortPair(self, n):
        self.inputs.remove(self.inputs[n])
        self.outputs.remove(self.outputs[n])

    def getInternalPiping(self) -> _ip.InternalPiping:
        assert len(self.inputs) == len(self.outputs)

        pipes = []
        portItems = {}
        for i, (graphicalInputPort, graphicalOutputPort) in enumerate(zip(self.inputs, self.outputs)):
            inputPort = _mfn.PortItem("In", _mfn.PortItemDirection.INPUT)
            outputPort = _mfn.PortItem("Out", _mfn.PortItemDirection.OUTPUT)
            pipe = _mfn.Pipe(inputPort, outputPort, name=f"Side{i}")

            pipes.append(pipe)
            portItems[inputPort] = graphicalInputPort
            portItems[outputPort] = graphicalOutputPort

        return _ip.InternalPiping(pipes, portItems)
