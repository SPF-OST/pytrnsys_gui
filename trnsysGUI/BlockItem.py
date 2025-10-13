# pylint: disable=invalid-name

import typing as _tp

import PyQt5.QtCore as _qtc
import PyQt5.QtGui as _qtg
from PyQt5 import QtWidgets as _qtw

import trnsysGUI.PortItemBase as _pib
import trnsysGUI.blockItemModel as _bim
import trnsysGUI.idGenerator as _id
import trnsysGUI.images as _img
import trnsysGUI.internalPiping as _ip
import trnsysGUI.moveCommand as _mc


# pylint: disable = fixme
# TODO : TeePiece and AirSourceHp size ratio need to be fixed, maybe just use original
#  svg instead of modified ones, TVentil is flipped. heatExchangers are also wrongly oriented
class BlockItem(
    _qtw.QGraphicsItem
):  # pylint: disable = too-many-public-methods, too-many-instance-attributes
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

        # To set flags of this item
        self.setFlags(self.ItemIsSelectable | self.ItemIsMovable)
        self.setFlag(self.ItemSendsScenePositionChanges, True)
        self.setCursor(_qtg.QCursor(_qtc.Qt.PointingHandCursor))

        self.label = _qtw.QGraphicsTextItem(self.displayName, self)
        self.label.setVisible(False)

        # Experimental, used for detecting genereated blocks attached to storage ports
        self.inFirstRow = False

        # Undo framework related
        self.oldPos = None

        self.origOutputsPos: _tp.Sequence[_tp.Sequence[int]] | None = None
        self.origInputsPos: _tp.Sequence[_tp.Sequence[int]] | None = None

        # TODO: The fact that we're assigning to a method is bad, but can't deal with it now
        self.isSelected = False  # type: ignore[method-assign,assignment]

    def _getImageAccessor(self) -> _tp.Optional[_img.ImageAccessor]:
        if isinstance(self, BlockItem):
            raise AssertionError(
                "`BlockItem' cannot be instantiated directly."
            )

        currentClassName = BlockItem.__name__
        currentMethodName = (
            f"{currentClassName}.{BlockItem._getImageAccessor.__name__}"
        )

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

    @_tp.override
    def boundingRect(self) -> _qtc.QRectF:
        return _qtc.QRectF(0, 0, self.w, self.h)

    # Setter functions
    def setParent(self, p):
        self.editor = p

    def setDisplayName(self, newName: str) -> None:
        self.displayName = newName
        self.label.setPlainText(newName)

    # Interaction related
    def contextMenuEvent(self, event):
        menu = _qtw.QMenu()

        rotateCwAction = menu.addAction(
            _img.ROTATE_TO_RIGHT_PNG.icon(), "Rotate Block clockwise"
        )
        rotateCwAction.triggered.connect(self.rotateBlockCW)

        rotateCcwAction = menu.addAction(
            _img.ROTATE_LEFT_PNG.icon(), "Rotate Block counter-clockwise"
        )
        rotateCcwAction.triggered.connect(self.rotateBlockCCW)

        resetRotationAction = menu.addAction("Reset Rotation")
        resetRotationAction.triggered.connect(self.resetRotation)

        deleteBlockAction = menu.addAction("Delete this Block")
        deleteBlockAction.triggered.connect(self.deleteBlockCom)

        self._addChildContextMenuActions(menu)

        menu.exec_(event.screenPos())

    def _addChildContextMenuActions(self, contextMenu: _qtw.QMenu) -> None:
        pass

    def mouseDoubleClickEvent(
        self,
        event: _qtw.QGraphicsSceneMouseEvent,  # pylint: disable=unused-argument
    ) -> None:
        self.editor.showBlockDlg(self)

    def mousePressEvent(self, event):
        self.isSelected = True
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        newPos = self.scenePos()

        oldPos = self.oldPos
        self.oldPos = newPos

        if oldPos is None or newPos == oldPos:
            return

        command = _mc.MoveCommand(
            self,
            oldScenePos=oldPos,
            newScenePos=newPos,
            descr="Move BlockItem",
        )
        self.editor.parent().undoStack.push(command)

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

    def updateFlipStateH(self, state: bool) -> None:
        self.flippedH = bool(state)
        self._updateTransform()

    def updateFlipStateV(self, state: bool) -> None:
        self.flippedV = bool(state)
        self._updateTransform()

    def rotateBlockCW(self):
        self.rotateBlockToN(1)

    def rotateBlockCCW(self):
        self.rotateBlockToN(-1)

    def rotateBlockToN(self, n: int) -> None:
        nQuarterTurns = self.rotationN + n
        self._rotateBlock(nQuarterTurns)

    def resetRotation(self):
        self._rotateBlock(0)

    def _rotateBlock(self, nQuarterTurns: int) -> None:
        self.rotationN = nQuarterTurns
        self.label.setRotation(-self.rotationN * 90)
        self._updateTransform()

    def _updateTransform(self) -> None:
        scaleX = -1 if self.flippedH else 1
        scaleY = -1 if self.flippedV else 1

        scale = _qtg.QTransform.fromScale(scaleX, scaleY)

        translateX = self.h if self.flippedH else 0
        translateY = self.w if self.flippedV else 0
        translate = _qtg.QTransform.fromTranslate(translateX, translateY)

        angle = self.rotationN * 90
        rotate = _qtg.QTransform().rotate(angle)

        transform = scale * translate * rotate  # type: ignore[operator]

        self.setTransform(transform)

    def deleteBlock(self):
        self.editor.trnsysObj.remove(self)
        self.editor.diagramScene.removeItem(self)

    def deleteBlockCom(self):
        self.editor.diagramView.deleteBlockCom(self)

    def updateImage(self):
        if self.flippedH:
            self.updateFlipStateH(self.flippedH)

        if self.flippedV:
            self.updateFlipStateV(self.flippedV)

    # AlignMode related
    def itemChange(self, change, value):
        # Snap grid excludes alignment

        if change == self.ItemPositionChange:
            if self.editor.snapGrid:
                snapSize = self.editor.snapSize
                self.logger.debug("itemchange")
                self.logger.debug(type(value))
                value = _qtc.QPointF(
                    value.x() - value.x() % snapSize,
                    value.y() - value.y() % snapSize,
                )
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
                    value = _qtc.QPointF(self.pos().x(), t.pos().y())
                    self.editor.alignYLineItem.setLine(
                        self.pos().x() + self.w / 2,
                        t.pos().y(),
                        t.pos().x() + t.w / 2,
                        t.pos().y(),
                    )

                    self.editor.alignYLineItem.setVisible(True)

                    qtm = _qtc.QTimer(self.editor)
                    qtm.timeout.connect(self.timerfunc)
                    qtm.setSingleShot(True)
                    qtm.start(1000)

                    e = _qtg.QMouseEvent(
                        _qtc.QEvent.MouseButtonRelease,
                        self.pos(),
                        _qtc.Qt.NoButton,
                        _qtc.Qt.NoButton,
                        _qtc.Qt.NoModifier,
                    )
                    self.editor.diagramView.mouseReleaseEvent(e)
                    self.editor.alignMode = False

                if self.elementInXBand(t):
                    value = _qtc.QPointF(t.pos().x(), self.pos().y())
                    self.editor.alignXLineItem.setLine(
                        t.pos().x(),
                        t.pos().y() + self.w / 2,
                        t.pos().x(),
                        self.pos().y() + t.w / 2,
                    )

                    self.editor.alignXLineItem.setVisible(True)

                    qtm = _qtc.QTimer(self.editor)
                    qtm.timeout.connect(self.timerfunc2)
                    qtm.setSingleShot(True)
                    qtm.start(1000)

                    e = _qtg.QMouseEvent(
                        _qtc.QEvent.MouseButtonRelease,
                        self.pos(),
                        _qtc.Qt.NoButton,
                        _qtc.Qt.NoButton,
                        _qtc.Qt.NoModifier,
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

    def elementInYBand(self, t):
        eps = 50
        return (
            self.scenePos().y() - eps
            <= t.scenePos().y()
            <= self.scenePos().y() + eps
        )

    def elementInXBand(self, t):
        eps = 50
        return (
            self.scenePos().x() - eps
            <= t.scenePos().x()
            <= self.scenePos().x() + eps
        )

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

    def _decodeBaseModel(
        self, blockItemModel: _bim.BlockItemBaseModel
    ) -> None:
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
        self.setPos(
            float(model.blockPosition[0]), float(model.blockPosition[1])
        )
        self.trnsysId = model.trnsysId

        if len(self.inputs) != len(model.portsIdsIn) or len(
            self.outputs
        ) != len(model.portsIdsOut):
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

    def exportMassFlows(self):
        return "", 0

    def exportDivSetting1(self):
        return "", 0

    def exportDivSetting2(self, nUnit):
        return "", nUnit

    def exportPipeAndTeeTypesForTemp(
        self, startingUnit: int
    ) -> _tp.Tuple[str, int]:
        return "", startingUnit

    def assignIDsToUninitializedValuesAfterJsonFormatMigration(
        self, generator: _id.IdGenerator
    ) -> None:
        pass

    def getInternalPiping(self) -> _ip.InternalPiping:
        raise NotImplementedError()
