import os
from math import sqrt

from PyQt5 import QtCore
from PyQt5.QtCore import QSize, QPointF, QPoint, QEvent, QTimer
from PyQt5.QtGui import QPixmap, QIcon, QImage, QCursor, QMouseEvent
from PyQt5.QtWidgets import QGraphicsPixmapItem, QGraphicsTextItem, QMenu

# from trnsysGUI.DeleteBlockCommand import DeleteBlockCommand
from trnsysGUI.PortItem import PortItem
from trnsysGUI.GroupChooserBlockDlg import GroupChooserBlockDlg
from trnsysGUI.MoveCommand import MoveCommand

from PyQt5.QtWidgets import QUndoCommand

# from trnsysGUI.Collector import Collector
# from trnsysGUI.Connector import Connector
# from trnsysGUI.GenericBlock import GenericBlock
# from trnsysGUI.HeatPump import HeatPump
# from trnsysGUI.HeatPumpTwoHx import HeatPumpTwoHx
# from trnsysGUI.IceStorage import IceStorage
# from trnsysGUI.Pump import Pump
# from trnsysGUI.Radiator import Radiator
# from trnsysGUI.StorageTank import StorageTank
# from trnsysGUI.TVentil import TVentil
# from trnsysGUI.TeePiece import TeePiece
# from trnsysGUI.WTap import WTap
# from trnsysGUI.WTap_main import WTap_main
from trnsysGUI.ResizerItem import ResizerItem
from trnsysGUI.TVentilDlg import TVentilDlg

global FilePath
FilePath = "res/Config.txt"

def calcDist(p1, p2):
    vec = p1 - p2
    norm = sqrt(vec.x() ** 2 + vec.y() ** 2)
    return norm

# TODO : TeePiece and AirSourceHp size ratio need to be fixed, maybe just use original
#  svg instead of modified ones, TVentil is flipped. heatExchangers are also wrongly oriented
class BlockItem(QGraphicsPixmapItem):

    def __init__(self, trnsysType, parent, **kwargs):

        super(BlockItem, self).__init__(None)
        self.w = 100.0
        self.h = 100.0
        self.parent = parent
        self.id = self.parent.parent().idGen.getID()
        self.propertyFile = []

        if "displayName" in kwargs:
            self.displayName = kwargs["displayName"]
        else:
            self.displayName = trnsysType + str(self.id)

        if "loadedBlock" not in kwargs:
            self.parent.parent().trnsysObj.append(self)

        self.groupName = ''
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

        # This case is because loaded blocks have parent=None
        # if self.parent is not None:
        #     self.parent.parent().trnsysObj.append(self)

        # Transform related
        self.flippedV = False
        self.flippedH = False
        self.rotationN = 0
        self.flippedHInt = -1
        self.flippedVInt = -1

        # self.imageSource = "images/" + self.name + ".png"
        # self.image = QImage("images/" + self.name)
        # self.pixmap = QPixmap(self.image)
        # self.setPixmap(self.pixmap.scaled(QSize(self.w, self.h)))

        # To use svg instead of png for blocks:
        self.imageSource = "images/" + self.name + ".svg"
        self.image = QImage(self.imageSource)
        self.setPixmap(QPixmap(self.image).scaled(QSize(self.w, self.h)))
        self.pixmap = QPixmap(self.image)

        # To set flags of this item
        self.setFlags(self.ItemIsSelectable | self.ItemIsMovable)
        self.setFlag(self.ItemSendsScenePositionChanges, True)
        self.setCursor(QCursor(QtCore.Qt.PointingHandCursor))

        self.label = QGraphicsTextItem(self.displayName, self)
        self.label.setVisible(False)

        if self.name == 'Bvi':
            self.inputs.append(PortItem('i', 0, self))
            self.outputs.append(PortItem('o', 2, self))

        if self.name == 'StorageTank':
            # Inputs get appended in ConfigStorage
            pass

        print("Block name is " + str(self.name))

        # Update size for generic block:
        if self.name == 'Bvi':
            self.changeSize()

        # Experimental, used for detecting genereated blocks attached to storage ports
        self.inFirstRow = False

        # Undo framework related
        self.oldPos = None

    # Setter functions
    def setParent(self, p):
        self.parent = p

        if self not in self.parent.parent().trnsysObj:
            self.parent.parent().trnsysObj.append(self)
            # print("trnsysObj are " + str(self.parent.parent().trnsysObj))

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
        # print("In setBlockToGroup")
        if newGroupName == self.groupName:
            print("Block " + str(self) + str(self.displayName) + "is already in this group")
            return
        else:
            # print("groups is " + str(self.parent.parent().groupList))
            for g in self.parent.parent().groupList:
                if g.displayName == self.groupName:
                    print("Found the old group " + self.groupName)
                    g.itemList.remove(self)
                if g.displayName == newGroupName:
                    # print("Found the new group " + newGroupName)
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

        lNtp = QIcon('images/Notebook.png')
        a1 = menu.addAction(lNtp, 'Launch NotePad++')
        a1.triggered.connect(self.launchNotepadFile)

        rr = QIcon('images/rotate-to-right.png')
        a2 = menu.addAction(rr, 'Rotate Block clockwise')
        a2.triggered.connect(self.rotateBlockCW)

        ll = QIcon('images/rotate-left.png')
        a3 = menu.addAction(ll, 'Rotate Block counter-clockwise')
        a3.triggered.connect(self.rotateBlockCCW)

        rRot = QIcon('images/move-left.png')
        a4 = menu.addAction(rRot, 'Reset Rotation')
        a4.triggered.connect(self.resetRotation)

        b1 = menu.addAction('Print Rotation')
        b1.triggered.connect(self.printRotation)

        dB = QIcon('images/close.png')
        c1 = menu.addAction(dB, 'Delete this Block')
        c1.triggered.connect(self.deleteBlockCom)

        # sG = QIcon('')
        c2 = menu.addAction("Set group")
        c2.triggered.connect(self.configGroup)

        d1 = menu.addAction('Dump information')
        d1.triggered.connect(self.dumpBlockInfo)

        e1 = menu.addAction('Inspect')
        e1.triggered.connect(self.inspectBlock)

        menu.exec_(event.screenPos())

    def launchNotepadFile(self):
        print("Launching notpad")
        global FilePath
        os.system('start notepad++ ' + FilePath)

    def mouseDoubleClickEvent(self, event):
        if hasattr(self, "isTempering"):
            dia = self.parent.parent().showTVentilDlg(self)
        elif self.name == 'Pump':
            dia = self.parent.parent().showPumpDlg(self)
        else:
            dia = self.parent.parent().showBlockDlg(self)
            if len(self.propertyFile) > 0:
                for files in self.propertyFile:
                    os.startfile(files, 'open')

    def mouseReleaseEvent(self, event):
        # print("Released mouse over block")
        if self.oldPos is None:
            print("For Undo Framework: oldPos is None")
        else:
            if self.scenePos() != self.oldPos:
                print("Block was dragged")
                print("Old pos is" + str(self.oldPos))
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

        if self.name == 'Bvi':
            self.inputs[0].setPos(-2 * delta + 4 * self.flippedH * delta + self.flippedH * w, h / 3)
            self.outputs[0].setPos(-2 * delta + 4 * self.flippedH * delta + self.flippedH * w, 2 * h / 3)
            self.inputs[0].side = 0 + 2 * self.flippedH
            self.outputs[0].side = 0 + 2 * self.flippedH

        return w, h

    def updateFlipStateH(self, state):
        self.pixmap = QPixmap(self.image.mirrored(bool(state), self.flippedV))
        self.setPixmap(self.pixmap.scaled(QSize(self.w, self.h)))
        self.flippedH = bool(state)
        if state == False:
            self.flippedHInt = -1
        else:
            self.flippedHInt = 1
        self.changeSize()

    def updateFlipStateV(self, state):
        self.pixmap = QPixmap(self.image.mirrored(self.flippedH, bool(state)))
        self.setPixmap(self.pixmap.scaled(QSize(self.w, self.h)))
        self.flippedV = bool(state)
        if state == False:
            self.flippedVInt = -1
        else:
            self.flippedVInt = 1
        self.changeSize()

    def updateSide(self, port, n):
        port.side = (port.side + n) % 4
        # print("Port side is " + str(port.side))

    def rotateBlockCW(self):
        # Rotate block clockwise
        # self.setTransformOriginPoint(50, 50)
        # self.setTransformOriginPoint(self.w/2, self.h/2)
        self.setTransformOriginPoint(0, 0)
        self.setRotation((self.rotationN + 1) * 90)
        self.rotationN += 1
        print("rotated by " + str(self.rotationN))

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
        self.rotationN -= 1
        print("rotated by " + str(self.rotationN))

        for p in self.inputs:
            p.itemChange(27, p.scenePos())
            self.updateSide(p, -1)

        for p in self.outputs:
            p.itemChange(27, p.scenePos())
            self.updateSide(p, -1)

    def resetRotation(self):
        print("Resetting rotation...")
        self.setRotation(0)

        for p in self.inputs:
            p.itemChange(27, p.scenePos())
            self.updateSide(p, -self.rotationN)
            # print("Portside of port " + str(p) + " is " + str(p.portSide))

        for p in self.outputs:
            p.itemChange(27, p.scenePos())
            self.updateSide(p, -self.rotationN)
            # print("Portside of port " + str(p) + " is " + str(p.portSide))

        self.rotationN = 0

    def printRotation(self):
        print("Rotation is " + str(self.rotationN))


    # Deletion related
    def deleteConns(self):

        for p in self.inputs:
            while len(p.connectionList) > 0:
                p.connectionList[0].deleteConn()

        for p in self.outputs:
            while len(p.connectionList) > 0:
                p.connectionList[0].deleteConn()

    def deleteBlock(self):
        print("Block " + str(self) + " is deleting itself (" + self.displayName + ")")
        self.deleteConns()
        # print("self.parent.parent" + str(self.parent.parent()))
        self.parent.parent().trnsysObj.remove(self)
        print("deleting block " + str(self) + self.displayName)
        # print("self.scene is" + str(self.parent.scene()))
        self.parent.scene().removeItem(self)
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

        Resizers are deleted inside mousePressEvent function inside core.py

        """
        print("Inside Block Item mouse click")
        if self.name == 'GenericBlock' or self.name == 'StorageTank':
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
        print("Inside block item set item size")
        self.w, self.h = w, h
        # if h < 20:
        #     self.h = 20
        # if w < 40:
        #     self.w = 40

    def updateImage(self):
        print("Inside block item update image")
        if self.imageSource[-3:] == "svg":
            # self.image = QImage(self.imageSource)
            self.setPixmap(QPixmap(self.image).scaled(QSize(self.w, self.h)))
            # self.setPixmap(QPixmap(self.image))
            self.pixmap = QPixmap(self.image)
            self.updateFlipStateH(self.flippedH)
            self.updateFlipStateV(self.flippedV)

        # elif self.imageSource[-3:] == "png":
        #     self.image = QImage(self.imageSource)
        #     self.setPixmap(QPixmap(self.image).scaled(QSize(self.w, self.h)))
        #     self.updateFlipStateH(self.flippedH)
        #     self.updateFlipStateV(self.flippedV)

    def deleteResizer(self):
        try:
            self.resizer
        except AttributeError:
            print("No resizer")
        else:
            del self.resizer


    # Debug
    def dumpBlockInfo(self):
        # for a in inspect.getMembers(self):
        #     print(str(a))

        print("This is a dump of " + str(self))
        print("Name = " + str(self.displayName))
        print("TrnsysType = " + str(self.name))
        print("TrnsysTypeNumber = " + str(self.typeNumber))
        print("Size = " + str(self.w) + " * " + str(self.h))

        self.printIds()
        self.printConnections()

    def printIds(self):
        print("ID:" + str(self.id))
        print("TrnsysID: " + str(self.trnsysId))

        for inp in self.inputs:
            print("Has input with ID " + str(inp.id))

        for out in self.outputs:
            print("Has output with ID " + str(out.id))

    def printConnections(self):
        print("Connections are:")
        for c in self.getConnections():
            print(c.displayName + " with ID " + str(c.id))

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
        # print(change, value)
        # Snap grid excludes alignment

        if change == self.ItemPositionChange:
            if self.parent.parent().snapGrid:
                snapSize = self.parent.parent().snapSize
                print("itemchange")
                print(type(value))
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
                    self.parent.parent().alignYLineItem.setLine(self.pos().x() + self.w/2, t.pos().y(), t.pos().x() + t.w/2, t.pos().y())

                    self.parent.parent().alignYLineItem.setVisible(True)

                    qtm = QTimer(self.parent.parent())
                    qtm.timeout.connect(self.timerfunc)
                    qtm.setSingleShot(True)
                    qtm.start(1000)

                    e = QMouseEvent(QEvent.MouseButtonRelease, self.pos(), QtCore.Qt.NoButton, QtCore.Qt.NoButton, QtCore.Qt.NoModifier)
                    self.parent.mouseReleaseEvent(e)
                    self.parent.parent().alignMode = False
                    # self.setPos(self.pos().x(), t.pos().y())
                    # self.aligned = True

                if self.elementInXBand(t):
                    value = QPointF(t.pos().x(), self.pos().y())
                    self.parent.parent().alignXLineItem.setLine(t.pos().x(), t.pos().y() + self.w / 2,
                                                                t.pos().x(), self.pos().y() + t.w / 2)

                    self.parent.parent().alignXLineItem.setVisible(True)

                    qtm = QTimer(self.parent.parent())
                    qtm.timeout.connect(self.timerfunc2)
                    qtm.setSingleShot(True)
                    qtm.start(1000)

                    e = QMouseEvent(QEvent.MouseButtonRelease, self.pos(), QtCore.Qt.NoButton, QtCore.Qt.NoButton,
                                    QtCore.Qt.NoModifier)
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

            dct['.__BlockDict__'] = True
            dct['BlockName'] = self.name
            dct['BlockDisplayName'] = self.displayName
            dct['BlockPosition'] = (float(self.pos().x()), float(self.pos().y()))
            dct['ID'] = self.id
            dct['trnsysID'] = self.trnsysId
            dct['PortsIDIn'] = portListInputs
            dct['PortsIDOut'] = portListOutputs
            dct['FlippedH'] = self.flippedH
            dct['FlippedV'] = self.flippedV
            dct['RotationN'] = self.rotationN
            dct['GroupName'] = self.groupName

            dictName = "Block-"

            return dictName, dct

    def decode(self, i, resConnList, resBlockList):
        self.setPos(float(i["BlockPosition"][0]), float(i["BlockPosition"][1]))
        self.trnsysId = i["trnsysID"]
        self.id = i["ID"]
        self.updateFlipStateH(i["FlippedH"])
        self.updateFlipStateV(i["FlippedV"])
        self.rotateBlockToN(i["RotationN"])
        # self.displayName = i["BlockDisplayName"]
        # self.label.setPlainText(self.displayName)
        self.setName(i["BlockDisplayName"])

        self.groupName = "defaultGroup"
        self.setBlockToGroup(i["GroupName"])

        print(len(self.inputs))
        for x in range(len(self.inputs)):
            self.inputs[x].id = i["PortsIDIn"][x]

        for x in range(len(self.outputs)):
            self.outputs[x].id = i["PortsIDOut"][x]

        resBlockList.append(self)

    def decodePaste(self, i, offset_x, offset_y, resConnList, resBlockList, **kwargs):
        self.setPos(float(i["BlockPosition"][0] + offset_x),
                  float(i["BlockPosition"][1] + offset_y))

        self.updateFlipStateH(i["FlippedH"])
        self.updateFlipStateV(i["FlippedV"])
        self.rotateBlockToN(i["RotationN"])

        for x in range(len(self.inputs)):
            self.inputs[x].id = i["PortsIDIn"][x]

        for x in range(len(self.outputs)):
            self.outputs[x].id = i["PortsIDOut"][x]

        resBlockList.append(self)


    # Export related
    def exportParameterSolver(self, descConnLength):
        temp = ""
        for i in self.inputs:
            # ConnectionList lenght should be max offset
            for c in i.connectionList:
                if hasattr(c.fromPort.parent, "heatExchangers") and i.connectionList.index(c) == 0:
                    continue
                elif hasattr(c.toPort.parent, "heatExchangers") and i.connectionList.index(c) == 0:
                    continue
                else:
                    temp = temp + str(c.trnsysId) + " "
                    self.trnsysConn.append(c)

        for o in self.outputs:
            # ConnectionList lenght should be max offset
            for c in o.connectionList:
                if type(c.fromPort.parent, "heatExchangers") and o.connectionList.index(c) == 0:
                    continue
                elif type(c.toPort.parent, "heatExchangers") and o.connectionList.index(c) == 0:
                    continue
                else:
                    temp = temp + str(c.trnsysId) + " "
                    self.trnsysConn.append(c)

        temp += str(self.typeNumber)
        temp += " " * (descConnLength - len(temp))
        self.exportConnsString = temp

        return temp + "!" + str(self.trnsysId) + " : " + str(self.displayName) + "\n"

    def exportBlackBox(self):
        # if len(t.inputs + t.outputs) == 2 and not isinstance(self, Connector):
        if len(self.inputs + self.outputs) == 2 and self.isVisible():
            resStr = "T" + self.displayName + "=1 \n"
            equationNr = 1

            return resStr, equationNr
        else:
            return "", 0

    def exportPumpOutlets(self):
        return "", 0

    def exportMassFlows(self):
        return "", 0

    def exportDivSetting1(self):
        return "", 0

    def exportDivSetting2(self, nUnit):
        return "", nUnit

    def exportParametersFlowSolver(self, descConnLength):
        # descConnLength = 20
        temp = ""
        for i in self.inputs:
            # ConnectionList lenght should be max offset
            for c in i.connectionList:
                if hasattr(c.fromPort.parent, "heatExchangers") and i.connectionList.index(c) == 0:
                    continue
                elif hasattr(c.toPort.parent, "heatExchangers") and i.connectionList.index(c) == 0:
                    continue
                else:
                    temp = temp + str(c.trnsysId) + " "
                    self.trnsysConn.append(c)

        for o in self.outputs:
            # ConnectionList lenght should be max offset
            for c in o.connectionList:
                if hasattr(c.fromPort.parent, "heatExchangers") and o.connectionList.index(c) == 0:
                    continue
                elif hasattr(c.toPort.parent, "heatExchangers") and o.connectionList.index(c) == 0:
                    continue
                else:
                    temp = temp + str(c.trnsysId) + " "
                    self.trnsysConn.append(c)

        temp += "0 "
        temp += str(self.typeNumber)
        temp += " " * (descConnLength - len(temp))
        self.exportConnsString = temp

        f = temp + "!" + str(self.trnsysId) + " : " + str(self.displayName) + "\n"

        return f, 1

    def exportInputsFlowSolver1(self):
        return "0,0 ", 1

    def exportInputsFlowSolver2(self):
        # return str(self.exportInitialInput) + " [" + self.displayName + "]", 1
        return str(self.exportInitialInput) + " ", 1

    def exportOutputsFlowSolver(self, prefix, abc, equationNumber, simulationUnit):
        tot = ""
        for i in range(0, 3):
            if i < 2:
                temp = prefix + self.displayName + "_" + abc[i] + "=[" + str(simulationUnit) + "," + \
                       str(equationNumber) + "]\n"
                tot += temp
                self.exportEquations.append(temp)
                # nEqUsed += 1  # DC
            equationNumber += 1  # DC-ERROR it should count anyway

        return tot, equationNumber, 2

    def exportPipeAndTeeTypesForTemp(self, startingUnit):
        return "", startingUnit
    
    def cleanUpAfterTrnsysExport(self):
        self.exportConnsString = ""
        self.exportInputName = "0"
        # self.exportInitialInput = -1
        self.exportEquations = []
        self.trnsysConn = []
