import os
from math import sqrt

from PyQt5 import QtCore
from PyQt5.QtCore import QSize, QPointF, QPoint, QEvent, QTimer
from PyQt5.QtGui import QPixmap, QIcon, QImage, QCursor, QMouseEvent
from PyQt5.QtWidgets import QGraphicsPixmapItem, QGraphicsTextItem, QMenu

from trnsysGUI.BlockDlg import BlockDlg
# from trnsysGUI.DeleteBlockCommand import DeleteBlockCommand
import trnsysGUI.DeleteBlockCommand

from trnsysGUI.PortItem import PortItem
from trnsysGUI.GroupChooserDlg import GroupChooserBlockDlg
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
from trnsysGUI.TVentilDlg import TVentilDlg

global FilePath
FilePath = "res/Config.txt"

def calcDist(p1, p2):
    vec = p1 - p2
    norm = sqrt(vec.x() ** 2 + vec.y() ** 2)
    return norm


class BlockItem(QGraphicsPixmapItem):

    def __init__(self, trnsysType, parent, **kwargs):

        super(BlockItem, self).__init__(None)
        self.w = 100.0
        self.h = 100.0
        self.parent = parent
        self.id = self.parent.parent().idGen.getID()

        if "displayName" in kwargs:
            self.displayName = kwargs["displayName"]
        else:
            self.displayName = trnsysType + str(self.id)

        if "loadedBlock" not in kwargs:
            self.parent.parent().trnsysObj.append(self)

        # print("Setting the displayName of " + str(self) + "to " + self.displayName)

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

        self.image = QImage("images/" + self.name)
        self.pixmap = QPixmap(self.image)
        self.setPixmap(self.pixmap.scaled(QSize(self.w, self.h)))

        self.setFlags(self.ItemIsSelectable | self.ItemIsMovable)
        self.setCursor(QCursor(QtCore.Qt.PointingHandCursor))

        self.label = QGraphicsTextItem(self.displayName, self)

        if self.name == 'Bvi':
            self.inputs.append(PortItem('i', 0, self))
            self.outputs.append(PortItem('o', 2, self))

        if self.name == 'StorageTank':
            # Inputs get appended in ConfigStorage
            pass

        self.setFlag(self.ItemSendsScenePositionChanges, True)

        print("self.name is " + str(self.name))

        # Update size for generic block:
        if self.name == 'Bvi':
            self.changeSize()

        # Experimental, used for detecting genereated blocks attached to storage ports
        self.inFirstRow = False

        # Undo framework related
        self.oldPos = None

    def setParent(self, p):
        self.parent = p

        if self not in self.parent.parent().trnsysObj:
            self.parent.parent().trnsysObj.append(self)
            # print("trnsysObj are " + str(self.parent.parent().trnsysObj))

    def setDefaultGroup(self):
        # self.groupName = "defaultGroup"
        # self.parent.parent().defaultGroup.addBlock(self)
        self.setBlockToGroup("defaultGroup")

    def setBlockToGroup(self, newGroupName):
        # print("In setBlockToGroup")
        if newGroupName == self.groupName:
            print("Block " + str(self) + str(self.displayName) + "is already in this group")
            return
        else:
            # print("groups is " + str(self.parent.parent().groupList))
            for g in self.parent.parent().groupList:
                print("At group " + str(g.displayName))
                print("self group is " + self.groupName)
                if g.displayName == self.groupName:
                    print("Found the old group " + self.groupName)
                    g.itemList.remove(self)
                if g.displayName == newGroupName:
                    print("Found the new group " + newGroupName)
                    g.itemList.append(self)

            self.groupName = newGroupName

    def setId(self, newId):
        self.id = newId

    def setName(self, newName):
        self.displayName = newName
        self.label.setPlainText(newName)

    def launchNotepadFile(self):
        print("Launching notpad")
        global FilePath
        os.system('start notepad++ ' + FilePath)

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
        self.changeSize()

    def updateFlipStateV(self, state):
        self.pixmap = QPixmap(self.image.mirrored(self.flippedH, bool(state)))
        self.setPixmap(self.pixmap.scaled(QSize(self.w, self.h)))
        self.flippedV = bool(state)
        self.changeSize()

    def mouseDoubleClickEvent(self, event):
        if hasattr(self, "isTempering"):
            dia = TVentilDlg(self, self.scene().parent())
        else:
            dia = BlockDlg(self, self.scene().parent())

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


    def getConnections(self):
        c = []
        for i in self.inputs:
            for cl in i.connectionList:
                c.append(cl)
        for o in self.outputs:
            for cl in o.connectionList:
                c.append(cl)
        return c

    def updateSide(self, port, n):
        port.side = (port.side + n) % 4
        # print("Port side is " + str(port.side))

    def rotateBlockCW(self):
        # Hacky rotation function
        self.setTransformOriginPoint(50, 50)
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
        # Hacky rotation function
        self.setTransformOriginPoint(50, 50)
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

    def configGroup(self):
        GroupChooserBlockDlg(self, self.parent.parent())

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

        return value

    def timerfunc(self):
        self.parent.parent().alignYLineItem.setVisible(False)

    def updateAlignment(self):
        pass

    def hasElementsInYBand(self):
        for t in self.parent.parent().trnsysObj:
            if isinstance(t, BlockItem):
                if self.elementInYBand(t):
                    return True

        return False

    def elementInYBand(self, t):
        eps = 50
        return self.scenePos().y() - eps <= t.scenePos().y() <= self.scenePos().y() + eps

    def elementInY(self):
        for t in self.parent.parent().trnsysObj:
            if isinstance(t, BlockItem):
                if self.scenePos().y == t.scenePos().y():
                    return True
        return False

    def deleteBlockCom(self):
        # command = trnsysGUI.DeleteBlockCommand.DeleteBlockCommand(self, "Delete block command")
        # self.parent.parent().parent().undoStack.push(command)
        self.parent.deleteBlockCom(self)

    def encode(self):
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
        self.displayName = i["BlockDisplayName"]
        self.label.setPlainText(self.displayName)

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

        # bl.trnsysId = i["trnsysID"]
        self.updateFlipStateH(i["FlippedH"])
        self.updateFlipStateV(i["FlippedV"])
        self.rotateBlockToN(i["RotationN"])

        for x in range(len(self.inputs)):
            self.inputs[x].id = i["PortsIDIn"][x]

        for x in range(len(self.outputs)):
            self.outputs[x].id = i["PortsIDOut"][x]

        resBlockList.append(self)

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

    def exportParametersFlowSolver(self):
        descConnLength = 20
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

        temp += str(self.typeNumber)
        temp += " " * (descConnLength - len(temp))
        self.exportConnsString = temp

        f = temp + "!" + str(self.trnsysId) + " : " + str(self.displayName) + "\n"

        return f, 1