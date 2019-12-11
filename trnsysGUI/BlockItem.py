import os
from math import sqrt

from PyQt5 import QtCore
from PyQt5.QtCore import QSize, QPointF
from PyQt5.QtGui import QPixmap, QIcon, QImage, QCursor
from PyQt5.QtWidgets import QGraphicsPixmapItem, QGraphicsTextItem, QMenu

from trnsysGUI.BlockDlg import BlockDlg
from trnsysGUI.PortItem import PortItem
from trnsysGUI.GroupChooserDlg import GroupChooserBlockDlg

global FilePath
FilePath = "res/Config.txt"

def calcDist(p1, p2):
    vec = p1 - p2
    norm = sqrt(vec.x() ** 2 + vec.y() ** 2)
    return norm


class BlockItem(QGraphicsPixmapItem):

    def __init__(self, trnsysType, name='Untitled', parent=None):
        super(BlockItem, self).__init__(None)
        self.w = 100.0
        self.h = 100.0
        self.parent = parent
        self.id = self.parent.parent().idGen.getID()

        # Temporary differentiation between new block and loaded block
        if trnsysType == name:
            # self.displayName = name[:-4] + str(self.id)
            self.displayName = name + str(self.id)
        else:
            self.displayName = name

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
        if self.parent is not None:
            self.parent.parent().trnsysObj.append(self)

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
        if self.name != 'TeePiece' and self.name != 'TVentil' and self.name != 'Pump' \
                and self.name != 'Kollektor' and self.name != 'HP' and self.name != 'IceStorage' \
                and self.name != 'Radiator' and self.name != 'WTap' and self.name != 'WTap_main' \
                and self.name != 'Connector':
            self.changeSize()

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
        c1.triggered.connect(self.deleteBlock)

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
        dia = BlockDlg(self, self.scene().parent())

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
            for c in p.connectionList:
                c.deleteConn()
        for p in self.outputs:
            for c in p.connectionList:
                c.deleteConn()

    def deleteBlock(self):
        print("Block " + str(self) + " is deleting itself (" + self.displayName + ")")
        self.deleteConns()
        print("self.parent.parent" + str(self.parent.parent()))
        self.parent.parent().trnsysObj.remove(self)
        print("deleting block " + str(self) + self.displayName)
        print("self.scene is" + str(self.parent.scene()))
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

    # def itemChange(self, change, value):
    #     # print(change, value)
    #     if change == self.ItemPositionHasChanged:
    #         print("itemcahgne")
    #         value = QPointF(value.x() - value.x() % 150, value.y() - value.y() % 150)
    #         return change, value
    #     else:
    #         return super(BlockItem, self).itemChange(change, value)