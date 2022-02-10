# pylint: skip-file
# type: ignore

import glob
import os
import typing as _tp

from PyQt5 import QtCore
from PyQt5.QtCore import QPointF, QEvent, QTimer
from PyQt5.QtGui import QPixmap, QCursor, QMouseEvent
from PyQt5.QtWidgets import QGraphicsPixmapItem, QGraphicsTextItem, QMenu, QTreeView

import trnsysGUI.createSinglePipePortItem as _cspi
import trnsysGUI.images as _img
from trnsysGUI import idGenerator as _id
from trnsysGUI.MoveCommand import MoveCommand
from trnsysGUI.ResizerItem import ResizerItem
from trnsysGUI.blockItemModel import BlockItemModel
from trnsysGUI.doublePipePortItem import DoublePipePortItem
from trnsysGUI.singlePipePortItem import SinglePipePortItem

global FilePath
FilePath = "res/Config.txt"


# TODO : TeePiece and AirSourceHp size ratio need to be fixed, maybe just use original
#  svg instead of modified ones, TVentil is flipped. heatExchangers are also wrongly oriented
class BlockItem(QGraphicsPixmapItem):
    def __init__(self, trnsysType, parent, displayNamePrefix = None, displayName = None, **kwargs):
        super().__init__(None)

        self.logger = parent.logger

        self.w = 120
        self.h = 120
        self.parent = parent
        self.id = self.parent.parent().idGen.getID()
        self.propertyFile = []

        if displayNamePrefix != None:
            self.displayName = displayNamePrefix + "_" + str(self.id)
        elif displayName != None:
            self.displayName = displayName
        else:
            raise Exception('No display name defined.')

        if "loadedBlock" not in kwargs:
            self.parent.parent().trnsysObj.append(self)

        self.inputs = []
        self.outputs = []

        # Export related:
        self.name = trnsysType
        self.trnsysId = self.parent.parent().idGen.getTrnsysID()

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

        if self.name == "Bvi":
            self.inputs.append(_cspi.createSinglePipePortItem("i", 0, self))
            self.outputs.append(_cspi.createSinglePipePortItem("o", 2, self))

        if self.name == "StorageTank":
            # Inputs get appended in ConfigStorage
            pass

        self.logger.debug("Block name is " + str(self.name))

        # Update size for generic block:
        if self.name == "Bvi":
            self.changeSize()

        # Experimental, used for detecting genereated blocks attached to storage ports
        self.inFirstRow = False

        # Undo framework related
        self.oldPos = None

        self.origOutputsPos = None
        self.origInputsPos = None

    def _getImageAccessor(self) -> _tp.Optional[_img.ImageAccessor]:
        if type(self) == BlockItem:
            raise AssertionError("`BlockItem' cannot be instantiated directly.")

        currentClassName = BlockItem.__name__
        currentMethodName = f"{currentClassName}.{BlockItem._getImageAccessor.__name__}"

        message = (
            f"{currentMethodName} has been called. However, this method should not be called directly but must\n"
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
        self.parent = p

        if self not in self.parent.parent().trnsysObj:
            self.parent.parent().trnsysObj.append(self)
            # self.logger.debug("trnsysObj are " + str(self.parent.parent().trnsysObj))

    def setId(self, newId):
        self.id = newId

    def setName(self, newName):
        self.displayName = newName
        self.label.setPlainText(newName)

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
        global FilePath
        os.system("start notepad++ " + FilePath)

    def mouseDoubleClickEvent(self, event):
        if hasattr(self, "isTempering"):
            self.parent.parent().showTVentilDlg(self)
        elif self.name == "Pump":
            self.parent.parent().showPumpDlg(self)
        elif self.name == "TeePiece" or self.name == "WTap_main":
            self.parent.parent().showBlockDlg(self)
        elif self.name in ["SPCnr", "DPCnr", "DPTee"]:
            self.parent.parent().showDoublePipeBlockDlg(self)
        else:
            self.parent.parent().showBlockDlg(self)
            if len(self.propertyFile) > 0:
                for files in self.propertyFile:
                    os.startfile(files, "open")

    def mouseReleaseEvent(self, event):
        # self.logger.debug("Released mouse over block")
        if self.oldPos is None:
            self.logger.debug("For Undo Framework: oldPos is None")
        else:
            if self.scenePos() != self.oldPos:
                self.logger.debug("Block was dragged")
                self.logger.debug("Old pos is" + str(self.oldPos))
                command = MoveCommand(self, self.oldPos, "Move BlockItem")
                self.parent.parent().parent().undoStack.push(command)
                self.oldPos = self.scenePos()

        super(BlockItem, self).mouseReleaseEvent(event)

    # Transform related
    def changeSize(self):
        self._positionLabel()

        w, h = self._getCappedWithAndHeight()

        if self.name == "Bvi":
            delta = 4

            self.inputs[0].setPos(-2 * delta + 4 * self.flippedH * delta + self.flippedH * w, h / 3)
            self.outputs[0].setPos(-2 * delta + 4 * self.flippedH * delta + self.flippedH * w, 2 * h / 3)
            self.inputs[0].side = 0 + 2 * self.flippedH
            self.outputs[0].side = 0 + 2 * self.flippedH

    def _positionLabel(self):
        width, height = self._getCappedWithAndHeight()
        rect = self.label.boundingRect()
        labelWidth, lableHeight = rect.width(), rect.height()
        labelPosX = (height - labelWidth) / 2
        self.label.setPos(labelPosX, width)

    def _getCappedWithAndHeight(self):
        width = self.w
        height = self.h
        if height < 20:
            height = 20
        if width < 40:
            width = 40
        return width, height

    def updateFlipStateH(self, state):
        self.flippedH = bool(state)

        pixmap = self._getPixmap()
        self.setPixmap(pixmap)

        self.flippedHInt = 1 if self.flippedH else -1

        if self.flippedH:
            for i in range(0, len(self.inputs)):
                distanceToMirrorAxis = self.w / 2.0 - self.origInputsPos[i][0]
                self.inputs[i].setPos(
                    self.origInputsPos[i][0] + 2.0 * distanceToMirrorAxis,
                    self.inputs[i].pos().y(),
                )

            for i in range(0, len(self.outputs)):
                distanceToMirrorAxis = self.w / 2.0 - self.origOutputsPos[i][0]
                self.outputs[i].setPos(
                    self.origOutputsPos[i][0] + 2.0 * distanceToMirrorAxis,
                    self.outputs[i].pos().y(),
                )

        else:
            for i in range(0, len(self.inputs)):
                self.inputs[i].setPos(self.origInputsPos[i][0], self.inputs[i].pos().y())

            for i in range(0, len(self.outputs)):
                self.outputs[i].setPos(self.origOutputsPos[i][0], self.outputs[i].pos().y())

    def updateFlipStateV(self, state):
        self.flippedV = bool(state)

        pixmap = self._getPixmap()
        self.setPixmap(pixmap)

        self.flippedVInt = 1 if self.flippedV else -1

        if self.flippedV:
            for i in range(0, len(self.inputs)):
                distanceToMirrorAxis = self.h / 2.0 - self.origInputsPos[i][1]
                self.inputs[i].setPos(
                    self.inputs[i].pos().x(),
                    self.origInputsPos[i][1] + 2.0 * distanceToMirrorAxis,
                )

            for i in range(0, len(self.outputs)):
                distanceToMirrorAxis = self.h / 2.0 - self.origOutputsPos[i][1]
                self.outputs[i].setPos(
                    self.outputs[i].pos().x(),
                    self.origOutputsPos[i][1] + 2.0 * distanceToMirrorAxis,
                )

        else:
            for i in range(0, len(self.inputs)):
                self.inputs[i].setPos(self.inputs[i].pos().x(), self.origInputsPos[i][1])

            for i in range(0, len(self.outputs)):
                self.outputs[i].setPos(self.outputs[i].pos().x(), self.origOutputsPos[i][1])

    def updateSidesFlippedH(self):
        if self.rotationN % 2 == 0:
            for p in self.inputs:
                if p.side == 0 or p.side == 2:
                    self.updateSide(p, 2)
            for p in self.outputs:
                if p.side == 0 or p.side == 2:
                    self.updateSide(p, 2)
        if self.rotationN % 2 == 1:
            for p in self.inputs:
                if p.side == 1 or p.side == 3:
                    self.updateSide(p, 2)
            for p in self.outputs:
                if p.side == 1 or p.side == 3:
                    self.updateSide(p, 2)

    def updateSidesFlippedV(self):
        if self.rotationN % 2 == 1:
            for p in self.inputs:
                if p.side == 0 or p.side == 2:
                    self.updateSide(p, 2)
            for p in self.outputs:
                if p.side == 0 or p.side == 2:
                    self.updateSide(p, 2)
        if self.rotationN % 2 == 0:
            for p in self.inputs:
                if p.side == 1 or p.side == 3:
                    self.updateSide(p, 2)
            for p in self.outputs:
                if p.side == 1 or p.side == 3:
                    self.updateSide(p, 2)

    def updateSide(self, port, n):
        port.side = (port.side + n) % 4
        # self.logger.debug("Port side is " + str(port.side))

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

    # Deletion related
    def deleteConns(self):

        for p in self.inputs:
            while len(p.connectionList) > 0:
                p.connectionList[0].deleteConn()

        for p in self.outputs:
            while len(p.connectionList) > 0:
                p.connectionList[0].deleteConn()

    def deleteBlock(self):
        self.parent.parent().trnsysObj.remove(self)
        self.parent.scene().removeItem(self)
        widgetToRemove = self.parent.parent().findChild(QTreeView, self.displayName + "Tree")
        if widgetToRemove:
            widgetToRemove.hide()

    def deleteBlockCom(self):
        self.parent.deleteBlockCom(self)

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
    def mousePressEvent(self, event):  # create resizer
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
        if self.name == "GenericBlock" or self.name == "StorageTank":
            return
        try:
            self.resizer
        except AttributeError:
            self.resizer = ResizerItem(self)
            self.resizer.setPos(self.w, self.h)
            self.resizer.itemChange(self.resizer.ItemPositionChange, self.resizer.pos())
        else:
            return

    def setItemSize(self, w, h):
        self.logger.debug("Inside block item set item size")
        self.w, self.h = w, h
        # if h < 20:
        #     self.h = 20
        # if w < 40:
        #     self.w = 40

    def updateImage(self):
        self.logger.debug("Inside block item update image")

        pixmap = self._getPixmap()
        self.setPixmap(pixmap)

        if self.flippedH:
            self.updateFlipStateH(self.flippedH)

        if self.flippedV:
            self.updateFlipStateV(self.flippedV)

    def _getPixmap(self) -> QPixmap:
        imageAccessor = self._getImageAccessor()

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
        # self.logger.debug(change, value)
        # Snap grid excludes alignment

        if change == self.ItemPositionChange:
            if self.parent.parent().snapGrid:
                snapSize = self.parent.parent().snapSize
                self.logger.debug("itemchange")
                self.logger.debug(type(value))
                value = QPointF(value.x() - value.x() % snapSize, value.y() - value.y() % snapSize)
                return value
            else:
                # if self.hasElementsInYBand() and not self.elementInY() and not self.aligned:
                if self.parent.parent().alignMode:
                    if self.hasElementsInYBand():
                        return self.alignBlock(value)
                    else:
                        # self.aligned = False
                        return value

                else:
                    return value
        else:
            return super(BlockItem, self).itemChange(change, value)

    def alignBlock(self, value):
        for t in self.parent.parent().trnsysObj:
            if isinstance(t, BlockItem) and t is not self:
                if self.elementInYBand(t):
                    value = QPointF(self.pos().x(), t.pos().y())
                    self.parent.parent().alignYLineItem.setLine(
                        self.pos().x() + self.w / 2, t.pos().y(), t.pos().x() + t.w / 2, t.pos().y()
                    )

                    self.parent.parent().alignYLineItem.setVisible(True)

                    qtm = QTimer(self.parent.parent())
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
                    self.parent.mouseReleaseEvent(e)
                    self.parent.parent().alignMode = False
                    # self.setPos(self.pos().x(), t.pos().y())
                    # self.aligned = True

                if self.elementInXBand(t):
                    value = QPointF(t.pos().x(), self.pos().y())
                    self.parent.parent().alignXLineItem.setLine(
                        t.pos().x(), t.pos().y() + self.w / 2, t.pos().x(), self.pos().y() + t.w / 2
                    )

                    self.parent.parent().alignXLineItem.setVisible(True)

                    qtm = QTimer(self.parent.parent())
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
                    self.parent.mouseReleaseEvent(e)
                    self.parent.parent().alignMode = False

        return value

    def timerfunc(self):
        self.parent.parent().alignYLineItem.setVisible(False)

    def timerfunc2(self):
        self.parent.parent().alignXLineItem.setVisible(False)

    def hasElementsInYBand(self):
        for t in self.parent.parent().trnsysObj:
            if isinstance(t, BlockItem):
                if self.elementInYBand(t):
                    return True

        return False

    def hasElementsInXBand(self):
        for t in self.parent.parent().trnsysObj:
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
        for t in self.parent.parent().trnsysObj:
            if isinstance(t, BlockItem):
                if self.scenePos().y == t.scenePos().y():
                    return True
        return False

    def encode(self):
        portListInputs = []
        portListOutputs = []

        for inp in self.inputs:
            portListInputs.append(inp.id)
        for output in self.outputs:
            portListOutputs.append(output.id)

        blockPosition = (float(self.pos().x()), float(self.pos().y()))

        blockItemModel = BlockItemModel(
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
        return dictName, blockItemModel.to_dict()

    def decode(self, i, resBlockList):
        model = BlockItemModel.from_dict(i)

        self.setName(model.BlockDisplayName)
        self.setPos(float(model.blockPosition[0]), float(model.blockPosition[1]))
        self.id = model.Id
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

    def decodePaste(self, i, offset_x, offset_y, resConnList, resBlockList, **kwargs):
        self.setPos(
            float(i["BlockPosition"][0] + offset_x),
            float(i["BlockPosition"][1] + offset_y),
        )

        self.updateFlipStateH(i["FlippedH"])
        self.updateFlipStateV(i["FlippedV"])
        self.rotateBlockToN(i["RotationN"])

        for x in range(len(self.inputs)):
            self.inputs[x].id = i["PortsIDIn"][x]

        for x in range(len(self.outputs)):
            self.outputs[x].id = i["PortsIDOut"][x]

        resBlockList.append(self)

    # Export related
    def exportBlackBox(self):
        equation = []
        if (
            len(self.inputs + self.outputs) == 2
            and self.isVisible()
            and not isinstance(self.outputs[0], DoublePipePortItem)
        ):
            files = glob.glob(os.path.join(self.path, "**/*.ddck"), recursive=True)
            if not (files):
                status = "noDdckFile"
            else:
                status = "noDdckEntry"
            lines = []
            for file in files:
                infile = open(file, "r")
                lines += infile.readlines()
            for i in range(len(lines)):
                if "output" in lines[i].lower() and "to" in lines[i].lower() and "hydraulic" in lines[i].lower():
                    for j in range(i, len(lines) - i):
                        if lines[j][0] == "T":
                            outputT = lines[j].split("=")[0].replace(" ", "")
                            status = "success"
                            break
                    equation = ["T" + self.displayName + "=" + outputT]
                    break
        else:
            status = "noBlackBoxOutput"

        if status == "noDdckFile" or status == "noDdckEntry":
            equation.append("T" + self.displayName + "=1")

        return status, equation

    def exportPumpOutlets(self):
        return "", 0

    def exportMassFlows(self):
        return "", 0

    def exportDivSetting1(self):
        return "", 0

    def exportDivSetting2(self, nUnit):
        return "", nUnit

    def exportPipeAndTeeTypesForTemp(self, startingUnit):
        return "", startingUnit

    def getTemperatureVariableName(self, portItem: SinglePipePortItem) -> str:
        return f"T{self.displayName}"

    def getFlowSolverParametersId(self, portItem: SinglePipePortItem) -> int:
        return self.trnsysId

    def assignIDsToUninitializedValuesAfterJsonFormatMigration(self, generator: _id.IdGenerator) -> None:
        pass

    def deleteLoadedFile(self):
        for items in self.loadedFiles:
            try:
                self.parent.parent().fileList.remove(str(items))
            except ValueError:
                self.logger.debug("File already deleted from file list.")
                self.logger.debug("filelist:", self.parent.parent().fileList)


