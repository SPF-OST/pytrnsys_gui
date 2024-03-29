# pylint: disable=invalid-name

import os
import typing as _tp

from PyQt5 import QtCore
from PyQt5.QtCore import QEvent
from PyQt5.QtCore import QPointF
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QCursor
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QGraphicsPixmapItem
from PyQt5.QtWidgets import QGraphicsTextItem
from PyQt5.QtWidgets import QMenu
from PyQt5.QtWidgets import QTreeView

import trnsysGUI.PortItemBase as _pib
import trnsysGUI.blockItemModel as _bim
import trnsysGUI.idGenerator as _id
import trnsysGUI.images as _img
import trnsysGUI.internalPiping as _ip
from trnsysGUI.MoveCommand import MoveCommand  # type: ignore[attr-defined]
from trnsysGUI.ResizerItem import ResizerItem  # type: ignore[attr-defined]

FILEPATH = "res/Config.txt"


# pylint: disable = fixme
# TODO : TeePiece and AirSourceHp size ratio need to be fixed, maybe just use original
#  svg instead of modified ones, TVentil is flipped. heatExchangers are also wrongly oriented
class BlockItem(QGraphicsPixmapItem):  # pylint: disable = too-many-public-methods, too-many-instance-attributes
    def __init__(self, trnsysType: str, editor, displayName: str) -> None:
        super().__init__(None)

        self.logger = editor.logger

        self.w = 120
        self.h = 120
        self.editor = editor

        if not displayName:
            raise ValueError("Display name cannot be empty.")

        self.displayName = displayName

        self.inputs: list[_pib.PortItemBase] = []
        self.outputs: list[_pib.PortItemBase] = []

        self.path: str | None = None

        # Export related:
        self.name = trnsysType
        self.trnsysId = self.editor.idGen.getTrnsysID()

        # Transform related
        self.flippedV = False
        self.flippedH = False
        self.rotationN = 0
        self.flippedHInt = -1
        self.flippedVInt = -1

        pixmap = self._getPixmap()
        self.setPixmap(pixmap)

        # To set flags of this item
        self.setFlags(self.ItemIsSelectable | self.ItemIsMovable)
        self.setFlag(self.ItemSendsScenePositionChanges, True)
        self.setCursor(QCursor(QtCore.Qt.PointingHandCursor))

        self.label = QGraphicsTextItem(self.displayName, self)
        self.label.setVisible(False)

        # Experimental, used for detecting genereated blocks attached to storage ports
        self.inFirstRow = False

        # Undo framework related
        self.oldPos = None

        self.origOutputsPos: _tp.Sequence[_tp.Sequence[int]] | None = None
        self.origInputsPos: _tp.Sequence[_tp.Sequence[int]] | None = None

    def _getImageAccessor(self) -> _tp.Optional[_img.ImageAccessor]:
        if isinstance(self, BlockItem):
            raise AssertionError("`BlockItem' cannot be instantiated directly.")

        currentClassName = BlockItem.__name__
        currentMethodName = f"{currentClassName}.{BlockItem._getImageAccessor.__name__}"

        message = (
            f"{currentMethodName} has been called. However, this method should not be called directly but must be\n"
            f"implemented in a child class. This means that a) someone instantiated `{currentClassName}` directly\n"
            f"or b) a child class of it doesn't implement `{currentMethodName}`. Either way that's an\n"
            f"unrecoverable error and therefore the program will be terminated now. Please do get in touch with\n"
            f"the developers if you've encountered this error. Thanks."
        )

        exception = AssertionError(message)

        # I've seen exception messages mysteriously swallowed that's why we're logging the message here, too.
        self.logger.error(message, exc_info=exception, stack_info=True)

        raise exception

    def addTree(self):
        pass

    # Setter functions
    def setParent(self, p):
        self.editor = p

    def setDisplayName(self, newName: str) -> None:
        self.displayName = newName
        self.label.setPlainText(newName)
        self._updateModels(newName)

    def _updateModels(self, newDisplayName: str) -> None:
        pass

    # Interaction related
    def contextMenuEvent(self, event):
        menu = QMenu()

        a1 = menu.addAction("Launch NotePad++")
        a1.triggered.connect(self.launchNotepadFile)

        rr = _img.ROTATE_TO_RIGHT_PNG.icon()
        a2 = menu.addAction(rr, "Rotate Block clockwise")
        a2.triggered.connect(self.rotateBlockCW)

        ll = _img.ROTATE_LEFT_PNG.icon()
        a3 = menu.addAction(ll, "Rotate Block counter-clockwise")
        a3.triggered.connect(self.rotateBlockCCW)

        a4 = menu.addAction("Reset Rotation")
        a4.triggered.connect(self.resetRotation)

        b1 = menu.addAction("Print Rotation")
        b1.triggered.connect(self.printRotation)

        c1 = menu.addAction("Delete this Block")
        c1.triggered.connect(self.deleteBlockCom)

        menu.exec_(event.screenPos())

    def launchNotepadFile(self):
        self.logger.debug("Launching notpad")
        os.system("start notepad++ " + FILEPATH)

    def mouseDoubleClickEvent(self, event):  # pylint: disable=unused-argument
        if hasattr(self, "isTempering"):
            self.editor.showTVentilDlg(self)
        elif self.name in ("TeePiece", "WTap_main"):
            self.editor.showBlockDlg(self)
        elif self.name in ["SPCnr", "DPCnr", "DPTee"]:
            self.editor.showDoublePipeBlockDlg(self)
        else:
            self.editor.showBlockDlg(self)

    def mouseReleaseEvent(self, event):
        # self.logger.debug("Released mouse over block")
        if self.oldPos is None:
            self.logger.debug("For Undo Framework: oldPos is None")
        else:
            if self.scenePos() != self.oldPos:
                self.logger.debug("Block was dragged")
                self.logger.debug("Old pos is" + str(self.oldPos))
                command = MoveCommand(self, self.oldPos, "Move BlockItem")
                self.editor.parent().undoStack.push(command)
                self.oldPos = self.scenePos()

        super().mouseReleaseEvent(event)

    # Transform related
    def changeSize(self):
        self._positionLabel()

    def _positionLabel(self):
        width, _ = self._getCappedWidthAndHeight()
        rect = self.label.boundingRect()
        labelWidth = rect.width()
        labelPosX = (width - labelWidth) / 2
        self.label.setPos(labelPosX, width)

    def _getCappedWidthAndHeight(self):
        width = self.w
        height = self.h
        height = max(height, 20)
        width = max(width, 40)
        return width, height

    def updateFlipStateH(self, state):
        self.flippedH = bool(state)

        pixmap = self._getPixmap()
        self.setPixmap(pixmap)

        self.flippedHInt = 1 if self.flippedH else -1

        if self.flippedH:
            for i, inputPort in enumerate(self.inputs):
                distanceToMirrorAxis = self.w / 2.0 - self.origInputsPos[i][0]  # pylint:disable=unsubscriptable-object
                inputPort.setPos(
                    self.origInputsPos[i][0] + 2.0 * distanceToMirrorAxis,  # pylint: disable = unsubscriptable-object
                    inputPort.pos().y(),
                )

            for i, outPort in enumerate(self.outputs):
                distanceToMirrorAxis = self.w / 2.0 - self.origOutputsPos[i][0]  # pylint:disable=unsubscriptable-object
                outPort.setPos(
                    self.origOutputsPos[i][0] + 2.0 * distanceToMirrorAxis,  # pylint: disable = unsubscriptable-object
                    outPort.pos().y(),
                )

        else:
            for i, inputPort in enumerate(self.inputs):
                inputPort.setPos(
                    self.origInputsPos[i][0], inputPort.pos().y()  # pylint: disable = unsubscriptable-object
                )

            for i, outputPort in enumerate(self.outputs):
                outputPort.setPos(
                    self.origOutputsPos[i][0], outputPort.pos().y()  # pylint: disable = unsubscriptable-object
                )

    def updateFlipStateV(self, state):
        self.flippedV = bool(state)

        pixmap = self._getPixmap()
        self.setPixmap(pixmap)

        self.flippedVInt = 1 if self.flippedV else -1

        if self.flippedV:
            for i, inputPort in enumerate(self.inputs):
                distanceToMirrorAxis = self.h / 2.0 - self.origInputsPos[i][1]  # pylint:disable=unsubscriptable-object
                inputPort.setPos(
                    inputPort.pos().x(),
                    self.origInputsPos[i][1] + 2.0 * distanceToMirrorAxis,  # pylint: disable = unsubscriptable-object
                )

            for i, outputPort in enumerate(self.outputs):
                distanceToMirrorAxis = self.h / 2.0 - self.origOutputsPos[i][1]  # pylint:disable=unsubscriptable-object
                outputPort.setPos(
                    outputPort.pos().x(),
                    self.origOutputsPos[i][1] + 2.0 * distanceToMirrorAxis,  # pylint: disable = unsubscriptable-object
                )

        else:
            for i, inputPort in enumerate(self.inputs):
                inputPort.setPos(
                    inputPort.pos().x(), self.origInputsPos[i][1]
                )  # pylint: disable = unsubscriptable-object

            for i, outputPort in enumerate(self.outputs):
                outputPort.setPos(
                    outputPort.pos().x(), self.origOutputsPos[i][1]
                )  # pylint: disable = unsubscriptable-object

    def updateSidesFlippedH(self):
        if self.rotationN % 2 == 0:
            for p in self.inputs:
                if p.side in (0, 2):
                    self.updateSide(p, 2)
            for p in self.outputs:
                if p.side in (0, 2):
                    self.updateSide(p, 2)
        if self.rotationN % 2 == 1:
            for p in self.inputs:
                if p.side in (1, 3):
                    self.updateSide(p, 2)
            for p in self.outputs:
                if p.side in (1, 3):
                    self.updateSide(p, 2)

    def updateSidesFlippedV(self):
        if self.rotationN % 2 == 1:
            for p in self.inputs:
                if p.side in (0, 2):
                    self.updateSide(p, 2)
            for p in self.outputs:
                if p.side in (0, 2):
                    self.updateSide(p, 2)
        if self.rotationN % 2 == 0:
            for p in self.inputs:
                if p.side in (1, 3):
                    self.updateSide(p, 2)
            for p in self.outputs:
                if p.side in (1, 3):
                    self.updateSide(p, 2)

    def updateSide(self, port, n):
        port.side = (port.side + n) % 4

    def rotateBlockCW(self):
        # Rotate block clockwise
        # self.setTransformOriginPoint(50, 50)
        # self.setTransformOriginPoint(self.w/2, self.h/2)
        self.setTransformOriginPoint(0, 0)
        self.setRotation((self.rotationN + 1) * 90)
        self.label.setRotation(-(self.rotationN + 1) * 90)
        self.rotationN += 1
        self.logger.debug("rotated by " + str(self.rotationN))

        for p in self.inputs:
            p.itemChange(27, p.scenePos())
            self.updateSide(p, 1)

        for p in self.outputs:
            p.itemChange(27, p.scenePos())
            self.updateSide(p, 1)

        pixmap = self._getPixmap()
        self.setPixmap(pixmap)

    def rotateBlockToN(self, n):
        if n > 0:
            while self.rotationN != n:
                self.rotateBlockCW()
        if n < 0:
            while self.rotationN != n:
                self.rotateBlockCCW()

    def rotateBlockCCW(self):
        # Rotate block clockwise
        # self.setTransformOriginPoint(50, 50)
        self.setTransformOriginPoint(0, 0)
        self.setRotation((self.rotationN - 1) * 90)
        self.label.setRotation(-(self.rotationN - 1) * 90)
        self.rotationN -= 1
        self.logger.debug("rotated by " + str(self.rotationN))

        for p in self.inputs:
            p.itemChange(27, p.scenePos())
            self.updateSide(p, -1)

        for p in self.outputs:
            p.itemChange(27, p.scenePos())
            self.updateSide(p, -1)

        pixmap = self._getPixmap()
        self.setPixmap(pixmap)

    def resetRotation(self):
        self.logger.debug("Resetting rotation...")
        self.setRotation(0)
        self.label.setRotation(0)

        for p in self.inputs:
            p.itemChange(27, p.scenePos())
            self.updateSide(p, -self.rotationN)
            # self.logger.debug("Portside of port " + str(p) + " is " + str(p.portSide))

        for p in self.outputs:
            p.itemChange(27, p.scenePos())
            self.updateSide(p, -self.rotationN)
            # self.logger.debug("Portside of port " + str(p) + " is " + str(p.portSide))

        self.rotationN = 0

        pixmap = self._getPixmap()
        self.setPixmap(pixmap)

    def printRotation(self):
        self.logger.debug("Rotation is " + str(self.rotationN))

    def deleteBlock(self):
        self.editor.trnsysObj.remove(self)
        self.editor.diagramScene.removeItem(self)
        widgetToRemove = self.editor.findChild(QTreeView, self.displayName + "Tree")
        if widgetToRemove:
            widgetToRemove.hide()

    def deleteBlockCom(self):
        self.editor.diagramView.deleteBlockCom(self)

    def getConnections(self):
        """
        Get the connections from inputs and outputs of this block.
        Returns
        -------
        c : :obj:`List` of :obj:`BlockItem`
        """
        c = []
        for i in self.inputs:
            for cl in i.connectionList:
                c.append(cl)
        for o in self.outputs:
            for cl in o.connectionList:
                c.append(cl)
        return c

    # Scaling related
    def mousePressEvent(self, event):  # pylint: disable = unused-argument
        """
        Using try catch to avoid creating extra resizers.

        When an item is clicked on, it will check if a resizer already existed. If
        there exist a resizer, returns. else, creates one.

        Resizer will not be created for GenericBlock due to complications in the code.
        Resizer will not be created for storageTank as there's already a built in function for it in the storageTank
        dialog.

        Resizers are deleted inside mousePressEvent function inside GUI.py

        """
        self.logger.debug("Inside Block Item mouse click")

        self.isSelected = True
        if self.name in ("GenericBlock", "StorageTank"):
            return
        try:
            self.resizer
        except AttributeError:
            self.resizer = ResizerItem(self)  # pylint: disable = attribute-defined-outside-init
            self.resizer.setPos(self.w, self.h)
            self.resizer.itemChange(self.resizer.ItemPositionChange, self.resizer.pos())

    def setItemSize(self, w, h):
        self.logger.debug("Inside block item set item size")
        self.w, self.h = w, h

    def updateImage(self):
        self.logger.debug("Inside block item update image")

        pixmap = self._getPixmap()
        self.setPixmap(pixmap)

        if self.flippedH:
            self.updateFlipStateH(self.flippedH)

        if self.flippedV:
            self.updateFlipStateV(self.flippedV)

    def _getPixmap(self) -> QPixmap:
        imageAccessor = self._getImageAccessor()  # pylint: disable = assignment-from-no-return

        assert imageAccessor

        image = imageAccessor.image(width=self.w, height=self.h).mirrored(
            horizontal=self.flippedH, vertical=self.flippedV
        )
        pixmap = QPixmap(image)

        return pixmap

    def deleteResizer(self):
        try:
            self.resizer
        except AttributeError:
            self.logger.debug("No resizer")
        else:
            del self.resizer

    # AlignMode related
    def itemChange(self, change, value):
        # Snap grid excludes alignment

        if change == self.ItemPositionChange:
            if self.editor.snapGrid:
                snapSize = self.editor.snapSize
                self.logger.debug("itemchange")
                self.logger.debug(type(value))
                value = QPointF(value.x() - value.x() % snapSize, value.y() - value.y() % snapSize)
                return value
            if self.editor.alignMode:
                if self.hasElementsInYBand():
                    return self.alignBlock(value)
            return value
        return super().itemChange(change, value)

    def alignBlock(self, value):
        for t in self.editor.trnsysObj:
            if isinstance(t, BlockItem) and t is not self:
                if self.elementInYBand(t):
                    value = QPointF(self.pos().x(), t.pos().y())
                    self.editor.alignYLineItem.setLine(
                        self.pos().x() + self.w / 2, t.pos().y(), t.pos().x() + t.w / 2, t.pos().y()
                    )

                    self.editor.alignYLineItem.setVisible(True)

                    qtm = QTimer(self.editor)
                    qtm.timeout.connect(self.timerfunc)
                    qtm.setSingleShot(True)
                    qtm.start(1000)

                    e = QMouseEvent(
                        QEvent.MouseButtonRelease,
                        self.pos(),
                        QtCore.Qt.NoButton,
                        QtCore.Qt.NoButton,
                        QtCore.Qt.NoModifier,
                    )
                    self.editor.diagramView.mouseReleaseEvent(e)
                    self.editor.alignMode = False

                if self.elementInXBand(t):
                    value = QPointF(t.pos().x(), self.pos().y())
                    self.editor.alignXLineItem.setLine(
                        t.pos().x(), t.pos().y() + self.w / 2, t.pos().x(), self.pos().y() + t.w / 2
                    )

                    self.editor.alignXLineItem.setVisible(True)

                    qtm = QTimer(self.editor)
                    qtm.timeout.connect(self.timerfunc2)
                    qtm.setSingleShot(True)
                    qtm.start(1000)

                    e = QMouseEvent(
                        QEvent.MouseButtonRelease,
                        self.pos(),
                        QtCore.Qt.NoButton,
                        QtCore.Qt.NoButton,
                        QtCore.Qt.NoModifier,
                    )
                    self.editor.diagramView.mouseReleaseEvent(e)
                    self.editor.alignMode = False

        return value

    def timerfunc(self):
        self.editor.alignYLineItem.setVisible(False)

    def timerfunc2(self):
        self.editor.alignXLineItem.setVisible(False)

    def hasElementsInYBand(self):
        for t in self.editor.trnsysObj:
            if isinstance(t, BlockItem):
                if self.elementInYBand(t):
                    return True

        return False

    def hasElementsInXBand(self):
        for t in self.editor.trnsysObj:
            if isinstance(t, BlockItem):
                if self.elementInXBand(t):
                    return True

        return False

    def elementInYBand(self, t):
        eps = 50
        return self.scenePos().y() - eps <= t.scenePos().y() <= self.scenePos().y() + eps

    def elementInXBand(self, t):
        eps = 50
        return self.scenePos().x() - eps <= t.scenePos().x() <= self.scenePos().x() + eps

    def elementInY(self):
        for t in self.editor.trnsysObj:
            if isinstance(t, BlockItem):
                if self.scenePos().y == t.scenePos().y():
                    return True
        return False

    def _encodeBaseModel(self) -> _bim.BlockItemBaseModel:
        position = (self.pos().x(), self.pos().y())

        blockItemModel = _bim.BlockItemBaseModel(
            position,
            self.trnsysId,
            self.flippedH,
            self.flippedV,
            self.rotationN,
        )

        return blockItemModel

    def _decodeBaseModel(self, blockItemModel: _bim.BlockItemBaseModel) -> None:
        x = float(blockItemModel.blockPosition[0])
        y = float(blockItemModel.blockPosition[1])
        self.setPos(x, y)

        self.trnsysId = blockItemModel.trnsysId

        self.updateFlipStateH(blockItemModel.flippedH)
        self.updateFlipStateV(blockItemModel.flippedV)

        self.rotateBlockToN(blockItemModel.rotationN)

    def encode(self):
        portListInputs = []
        portListOutputs = []

        for inp in self.inputs:
            portListInputs.append(inp.id)
        for output in self.outputs:
            portListOutputs.append(output.id)

        blockPosition = (float(self.pos().x()), float(self.pos().y()))

        blockItemModel = _bim.BlockItemModel(
            self.name,
            self.displayName,
            blockPosition,
            self.trnsysId,
            portListInputs,  # pylint: disable = duplicate-code # 1
            portListOutputs,
            self.flippedH,
            self.flippedV,
            self.rotationN,
        )

        dictName = "Block-"
        return dictName, blockItemModel.to_dict()

    def decode(self, i, resBlockList):
        model = _bim.BlockItemModel.from_dict(i)

        self.setDisplayName(model.BlockDisplayName)
        self.setPos(float(model.blockPosition[0]), float(model.blockPosition[1]))
        self.trnsysId = model.trnsysId

        if len(self.inputs) != len(model.portsIdsIn) or len(self.outputs) != len(model.portsIdsOut):
            temp = model.portsIdsIn
            model.portsIdsIn = model.portsIdsOut
            model.portsIdsOut = temp

        for index, inp in enumerate(self.inputs):
            inp.id = model.portsIdsIn[index]

        for index, out in enumerate(self.outputs):
            out.id = model.portsIdsOut[index]

        self.updateFlipStateH(model.flippedH)
        self.updateFlipStateV(model.flippedV)
        self.rotateBlockToN(model.rotationN)

        resBlockList.append(self)

    def exportPumpOutlets(self):
        return "", 0

    def exportMassFlows(self):
        return "", 0

    def exportDivSetting1(self):
        return "", 0

    def exportDivSetting2(self, nUnit):
        return "", nUnit

    def exportPipeAndTeeTypesForTemp(self, startingUnit: int) -> _tp.Tuple[str, int]:
        return "", startingUnit

    def assignIDsToUninitializedValuesAfterJsonFormatMigration(self, generator: _id.IdGenerator) -> None:
        pass

    def getInternalPiping(self) -> _ip.InternalPiping:
        raise NotImplementedError()

    def deleteLoadedFile(self):
        for items in self.loadedFiles:
            try:
                self.editor.fileList.remove(str(items))
            except ValueError:
                self.logger.debug("File already deleted from file list.")
                self.logger.debug("filelist:", self.editor.fileList)
