# pylint: skip-file
# type: ignore

import glob
import math
import os
import typing as _tp

from PyQt5 import QtCore
from PyQt5.QtCore import QPointF, QEvent, QTimer
from PyQt5.QtGui import QPixmap, QCursor, QMouseEvent
from PyQt5.QtWidgets import QGraphicsPixmapItem, QGraphicsTextItem, QMenu, QTreeView

import trnsysGUI.images as _img
import trnsysGUI.IdGenerator as _id
from trnsysGUI.MoveCommand import MoveCommand
from trnsysGUI.PortItem import PortItem
from trnsysGUI.ResizerItem import ResizerItem

global FilePath
FilePath = "res/Config.txt"


def calcDist(p1, p2):
    vec = p1 - p2
    norm = math.sqrt(vec.x() ** 2 + vec.y() ** 2)
    return norm


# TODO : TeePiece and AirSourceHp size ratio need to be fixed, maybe just use original
#  svg instead of modified ones, TVentil is flipped. heatExchangers are also wrongly oriented
class BlockItem(QGraphicsPixmapItem):
    def __init__(self, trnsysType, parent, **kwargs):
        super().__init__(None)

        self.logger = parent.logger

        self.w = 120
        self.h = 120
        self.parent = parent
        self.id = self.parent.parent().idGen.getID()
        self.propertyFile = []

        if "displayName" in kwargs:
            self.displayName = kwargs["displayName"]
        else:
            self.displayName = trnsysType + "_" + str(self.id)

        if "loadedBlock" not in kwargs:
            self.parent.parent().trnsysObj.append(self)

        self.groupName = ""
        self.setDefaultGroup()

        self.inputs = []
        self.outputs = []

        # Export related:
        self.name = trnsysType
        self.trnsysId = self.parent.parent().idGen.getTrnsysID()
        self.typeNumber = 0
        self.exportConnsString = ""
        self.exportInputName = "0"
        self.exportInitialInput = -1
        self.exportEquations = []
        self.trnsysConn = []

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
            self.inputs.append(PortItem("i", 0, self))
            self.outputs.append(PortItem("o", 2, self))

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

    # Setter functions
    def setParent(self, p):
        self.parent = p

        if self not in self.parent.parent().trnsysObj:
            self.parent.parent().trnsysObj.append(self)
            # self.logger.debug("trnsysObj are " + str(self.parent.parent().trnsysObj))

    def setDefaultGroup(self):
        """
        Sets the group to defaultGroup when being created.
        Returns
        -------

        """
        self.setBlockToGroup("defaultGroup")

    def setBlockToGroup(self, newGroupName):
        """
        Sets the groupName of this Block to newGroupName and appends itself to the itemList of that group
        Parameters
        ----------
        newGroupName

        Returns
        -------

        """
        # self.logger.debug("In setBlockToGroup")
        if newGroupName == self.groupName:
            self.logger.debug(
                "Block "
                + str(self)
                + str(self.displayName)
                + "is already in this group"
            )
            return
        else:
            # self.logger.debug("groups is " + str(self.parent.parent().groupList))
            for g in self.parent.parent().groupList:
                if g.displayName == self.groupName:
                    self.logger.debug("Found the old group " + self.groupName)
                    g.itemList.remove(self)
                if g.displayName == newGroupName:
                    # self.logger.debug("Found the new group " + newGroupName)
                    g.itemList.append(self)

            self.groupName = newGroupName

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
            dia = self.parent.parent().showTVentilDlg(self)
        elif self.name == "Pump":
            dia = self.parent.parent().showPumpDlg(self)
        elif self.name == "TeePiece" or self.name == "WTap_main":
            dia = self.parent.parent().showBlockDlg(self)
        else:
            dia = self.parent.parent().showBlockDlg(self)
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
        w = self.w
        h = self.h

        """ Resize block function """
        delta = 4

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

        if self.name == "Bvi":
            self.inputs[0].setPos(
                -2 * delta + 4 * self.flippedH * delta + self.flippedH * w, h / 3
            )
            self.outputs[0].setPos(
                -2 * delta + 4 * self.flippedH * delta + self.flippedH * w, 2 * h / 3
            )
            self.inputs[0].side = 0 + 2 * self.flippedH
            self.outputs[0].side = 0 + 2 * self.flippedH

        return w, h

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
                self.inputs[i].setPos(
                    self.origInputsPos[i][0], self.inputs[i].pos().y()
                )

            for i in range(0, len(self.outputs)):
                self.outputs[i].setPos(
                    self.origOutputsPos[i][0], self.outputs[i].pos().y()
                )

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
                self.inputs[i].setPos(
                    self.inputs[i].pos().x(), self.origInputsPos[i][1]
                )

            for i in range(0, len(self.outputs)):
                self.outputs[i].setPos(
                    self.outputs[i].pos().x(), self.origOutputsPos[i][1]
                )

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

    def resetRotation(self):
        self.logger.debug("Resetting rotation...")
        self.setRotation(0)

        for p in self.inputs:
            p.itemChange(27, p.scenePos())
            self.updateSide(p, -self.rotationN)
            # self.logger.debug("Portside of port " + str(p) + " is " + str(p.portSide))

        for p in self.outputs:
            p.itemChange(27, p.scenePos())
            self.updateSide(p, -self.rotationN)
            # self.logger.debug("Portside of port " + str(p) + " is " + str(p.portSide))

        self.rotationN = 0

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
        self.logger.debug(
            "Block " + str(self) + " is deleting itself (" + self.displayName + ")"
        )
        self.deleteConns()
        # self.logger.debug("self.parent.parent" + str(self.parent.parent()))
        self.parent.parent().trnsysObj.remove(self)
        self.logger.debug("deleting block " + str(self) + self.displayName)
        # self.logger.debug("self.scene is" + str(self.parent.scene()))
        self.parent.scene().removeItem(self)
        widgetToRemove = self.parent.parent().findChild(
            QTreeView, self.displayName + "Tree"
        )
        try:
            widgetToRemove.hide()
        except AttributeError:
            self.logger.debug("Widget doesnt exist!")
        else:
            self.logger.debug("Deleted widget")
        del self

    def deleteBlockCom(self):
        # command = trnsysGUI.DeleteBlockCommand.DeleteBlockCommand(self, "Delete block command")
        # self.parent.parent().parent().undoStack.push(command)
        self.parent.deleteBlockCom(self)

    def configGroup(self):
        """
        This method is called from the contextMenu and allows to pick a group for this block.
        Returns
        -------

        """
        self.parent.parent().showGroupChooserBlockDlg(self)

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

    # Debug
    def dumpBlockInfo(self):
        # for a in inspect.getMembers(self):
        #     self.logger.debug(str(a))

        self.logger.debug("This is a dump of " + str(self))
        self.logger.debug("Name = " + str(self.displayName))
        self.logger.debug("TrnsysType = " + str(self.name))
        self.logger.debug("TrnsysTypeNumber = " + str(self.typeNumber))
        self.logger.debug("Size = " + str(self.w) + " * " + str(self.h))

        self.printIds()
        self.printConnections()

    def printIds(self):
        self.logger.debug("ID:" + str(self.id))
        self.logger.debug("TrnsysID: " + str(self.trnsysId))

        for inp in self.inputs:
            self.logger.debug("Has input with ID " + str(inp.id))

        for out in self.outputs:
            self.logger.debug("Has output with ID " + str(out.id))

    def printConnections(self):
        self.logger.debug("Connections are:")
        for c in self.getConnections():
            self.logger.debug(c.displayName + " with ID " + str(c.id))

    def inspectBlock(self):
        self.parent.parent().listV.clear()
        self.parent.parent().listV.addItem("Name: " + self.name)
        self.parent.parent().listV.addItem("Display name: " + self.displayName)
        self.parent.parent().listV.addItem("Group name: " + self.groupName)
        self.parent.parent().listV.addItem("Parent: " + str(self.parent))
        self.parent.parent().listV.addItem("Position: " + str(self.pos()))
        self.parent.parent().listV.addItem("Sceneposition: " + str(self.scenePos()))
        self.parent.parent().listV.addItem("Inputs: " + str(self.inputs))
        self.parent.parent().listV.addItem("Outputs: " + str(self.outputs))

    # AlignMode related
    def itemChange(self, change, value):
        # self.logger.debug(change, value)
        # Snap grid excludes alignment

        if change == self.ItemPositionChange:
            if self.parent.parent().snapGrid:
                snapSize = self.parent.parent().snapSize
                self.logger.debug("itemchange")
                self.logger.debug(type(value))
                value = QPointF(
                    value.x() - value.x() % snapSize, value.y() - value.y() % snapSize
                )
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
                        self.pos().x() + self.w / 2,
                        t.pos().y(),
                        t.pos().x() + t.w / 2,
                        t.pos().y(),
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
                        t.pos().x(),
                        t.pos().y() + self.w / 2,
                        t.pos().x(),
                        self.pos().y() + t.w / 2,
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
        return (
            self.scenePos().y() - eps <= t.scenePos().y() <= self.scenePos().y() + eps
        )

    def elementInXBand(self, t):
        eps = 50
        return (
            self.scenePos().x() - eps <= t.scenePos().x() <= self.scenePos().x() + eps
        )

    def elementInY(self):
        for t in self.parent.parent().trnsysObj:
            if isinstance(t, BlockItem):
                if self.scenePos().y == t.scenePos().y():
                    return True
        return False

    # Encoding
    def encode(self):
        # Double check that no virtual block gets encoded
        if self.isVisible():
            portListInputs = []
            portListOutputs = []

            for p in self.inputs:
                portListInputs.append(p.id)
            for p in self.outputs:
                portListOutputs.append(p.id)
            dct = {}

            dct[".__BlockDict__"] = True
            dct["BlockName"] = self.name
            dct["BlockDisplayName"] = self.displayName
            dct["BlockPosition"] = (float(self.pos().x()), float(self.pos().y()))
            dct["ID"] = self.id
            dct["trnsysID"] = self.trnsysId
            dct["PortsIDIn"] = portListInputs
            dct["PortsIDOut"] = portListOutputs
            dct["FlippedH"] = self.flippedH
            dct["FlippedV"] = self.flippedV
            dct["RotationN"] = self.rotationN
            dct["GroupName"] = self.groupName

            dictName = "Block-"

            return dictName, dct

    def decode(self, i, resBlockList):
        self.setPos(float(i["BlockPosition"][0]), float(i["BlockPosition"][1]))
        self.trnsysId = i["trnsysID"]
        self.id = i["ID"]
        self.updateFlipStateH(i["FlippedH"])
        self.updateFlipStateV(i["FlippedV"])
        self.rotateBlockToN(i["RotationN"])
        self.setName(i["BlockDisplayName"])

        self.groupName = "defaultGroup"
        self.setBlockToGroup(i["GroupName"])

        self.logger.debug(len(self.inputs))

        if len(self.inputs) != len(i["PortsIDIn"]) or len(self.outputs) != len(
            i["PortsIDOut"]
        ):
            temp = i["PortsIDIn"]
            i["PortsIDIn"] = i["PortsIDOut"]
            i["PortsIDOut"] = temp

        for x in range(len(self.inputs)):
            self.inputs[x].id = i["PortsIDIn"][x]

        for x in range(len(self.outputs)):
            self.outputs[x].id = i["PortsIDOut"][x]

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
        if len(self.inputs + self.outputs) == 2 and self.isVisible():
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
                if (
                    "output" in lines[i].lower()
                    and "to" in lines[i].lower()
                    and "hydraulic" in lines[i].lower()
                ):
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

    def exportParametersFlowSolver(self, descConnLength):
        temp = ""
        for i in self.inputs:
            for c in i.connectionList:
                temp = temp + str(c.trnsysId) + " "
                self.trnsysConn.append(c)

        for o in self.outputs:
            for c in o.connectionList:
                temp = temp + str(c.trnsysId) + " "
                self.trnsysConn.append(c)

        temp += "0 "
        temp += str(self.typeNumber)
        temp += " " * (descConnLength - len(temp))
        self.exportConnsString = temp

        f = temp + "!" + str(self.trnsysId) + " : " + str(self.displayName) + "\n"

        return f

    def exportInputsFlowSolver1(self):
        return "0,0 ", 1

    def exportInputsFlowSolver2(self):
        return str(self.exportInitialInput) + " ", 1

    def exportOutputsFlowSolver(self, prefix, abc, equationNumber, simulationUnit):
        equation1 = self._createFlowSolverOutputEquation(0, abc, prefix, equationNumber, simulationUnit)
        equation2 = self._createFlowSolverOutputEquation(1, abc, prefix, equationNumber, simulationUnit)

        self.exportEquations.append(equation1)
        self.exportEquations.append(equation2)

        equations = equation1 + equation2
        nEquationsUsed = 2
        nextEquationNumber = equationNumber + 3

        return equations, nextEquationNumber, nEquationsUsed

    def _createFlowSolverOutputEquation(self, equationNumber, abc, prefix, equationNumberOffset, simulationUnit):
        return f"{prefix}{self.displayName}_{abc[equationNumber]}=[{simulationUnit},{equationNumberOffset + equationNumber}]\n"

    def exportPipeAndTeeTypesForTemp(self, startingUnit):
        return "", startingUnit

    def getTemperatureVariableName(self, portItem: PortItem) -> str:
        return f"T{self.displayName}"

    def getFlowSolverParametersId(self, portItem: PortItem) -> int:
        return self.trnsysId

    def assignIDsToUninitializedValuesAfterJsonFormatMigration(self, generator: _id.IdGenerator) -> None:
        pass

    def cleanUpAfterTrnsysExport(self):
        self.exportConnsString = ""
        self.exportInputName = "0"
        # self.exportInitialInput = -1
        self.exportEquations = []
        self.trnsysConn = []

    def deleteLoadedFile(self):
        for items in self.loadedFiles:
            try:
                self.parent.parent().fileList.remove(str(items))
            except ValueError:
                self.logger.debug("File already deleted from file list.")
                self.logger.debug("filelist:", self.parent.parent().fileList)
