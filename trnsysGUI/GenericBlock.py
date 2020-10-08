import os
import shutil
from pathlib import Path

from PyQt5.QtCore import QSize
from PyQt5.QtGui import QPixmap, QImage, QIcon
from PyQt5.QtWidgets import QMenu, QFileDialog, QTreeView

from trnsysGUI.BlockItem import BlockItem
from trnsysGUI.GenericPortPairDlg import GenericPortPairDlg
from trnsysGUI.MyQFileSystemModel import MyQFileSystemModel
from trnsysGUI.MyQTreeView import MyQTreeView
from trnsysGUI.PortItem import PortItem
# from trnsysGUI.newPortDlg import newPortDlg


class GenericBlock(BlockItem):
    def __init__(self, trnsysType, parent, **kwargs):
        super(GenericBlock, self).__init__(trnsysType, parent, **kwargs)

        self.inputs.append(PortItem('i', 2, self))
        self.outputs.append(PortItem('o', 2, self))
        self.loadedFiles = []

        self.pixmap = QPixmap(self.image)
        self.setPixmap(self.pixmap.scaled(QSize(self.w, self.h)))

        self.childIds = []
        self.childIds.append(self.trnsysId)

        self.subBlockCounter = 0

        self.imagesource = ("images/" + self.name)

        # Disallow adding port pairs later, because the trnsysIDs of the generated port pairs have to be
        # consecutive to be correctly printed out in the export
        self.isSet = True

        self.changeSize()
        self.addTree()

    def changeSize(self):
        # print("passing through c change size")
        w = self.w
        h = self.h
        delta = 4
        deltaH = self.h / 10

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

        self.outputs[0].setPos(2 * delta + w,
                               h - 2 * delta)
        self.inputs[0].setPos(2 * delta + w,
                              2 * delta)
        # self.inputs[0].side = 2 - 2 * self.flippedH
        # self.outputs[0].side = 2 - 2 * self.flippedH

        self.updatePortPos()
        return w, h

    def updatePortPos(self):
        delta = 4
        deltaH = self.h / 10
        w = self.w
        h = self.h

        # Update port positions:
        # self.outputs[0].setPos(2 * delta - 4 * self.flippedH * delta - self.flippedH * w + w,
        #                        h - h * self.flippedV - deltaH + 2 * deltaH * self.flippedV)
        # self.inputs[0].setPos(2 * delta - 4 * self.flippedH * delta - self.flippedH * w + w,
        #                       h * self.flippedV + deltaH - 2 * deltaH * self.flippedV)
        # self.inputs[0].side = 2 - 2 * self.flippedH
        # self.outputs[0].side = 2 - 2 * self.flippedH

        # Number of pairs on each side, starting left, clockwise
        pairNbs = [0, 0, 0, 0]
        for s in range(4):
            pairNbs[s] = self.getPairNb(s)

        portNb = [0, 0, 0, 0]
        for i in self.inputs:
            # This could be necessary if one were able to add ports when block not flipped/rotated
            # if i.initSide == 0:
            # Below, i.side == initside

            # if i.side == 0:
            #     distBetweenPorts = (self.h - 4*delta) / (2 * self.getPairNb(0) - 1)
            #     print("distance betw ports " + str(distBetweenPorts))
            #     i.setPos(- 2*delta + 4 * self.flippedH * delta + self.flippedH * w,
            #               2*delta + distBetweenPorts * portNb[0])
            #     i.side = 0 + 2 * self.flippedH
            #     portNb[0] += 1
            #
            #     self.outputs[self.inputs.index(i)].setPos(- 2*delta + 4 * self.flippedH * delta + self.flippedH * w,
            #                2*delta + distBetweenPorts * portNb[0])
            #     self.outputs[self.inputs.index(i)].side = 0 + 2 * self.flippedH
            #     portNb[0] += 1
            #
            # if i.side == 1:
            #     distBetweenPorts = (self.w - 4 * delta) / (2 * self.getPairNb(1) - 1)
            #     print("distance betw ports " + str(distBetweenPorts))
            #     i.setPos(2 * delta + distBetweenPorts * portNb[1],
            #              - 2 * delta + 4 * self.flippedV * delta + self.flippedV * h)
            #     i.side = 1 + 2 * self.flippedV
            #     portNb[1] += 1
            #
            #     self.outputs[self.inputs.index(i)].setPos(2 * delta + distBetweenPorts * portNb[1],
            #              - 2 * delta + 4 * self.flippedV * delta + self.flippedV * h)
            #     self.outputs[self.inputs.index(i)].side = 1 + 2 * self.flippedV
            #     portNb[1] += 1
            pass

    def getPairNb(self, side):
        res = 0
        for i in self.inputs:
            if i.side == side:
                res += 1

        print("there are " + str(res) + " pairs on the side "+ str(side))
        return res

    def addPortDlg(self):
        # newPortDlg(self, self.parent.parent())
        # dlg = GenericPortPairDlg(self, self.parent.parent())
        self.parent.parent().showGenericPortPairDlg(self)

    def addPort(self, io, relH):
        print(io)
        print(relH)

    def setImage(self, name):
        print("Setting image with name" + name)
        self.image = QImage(name)
        self.pixmap = QPixmap(self.image)
        self.setPixmap(self.pixmap.scaled(QSize(self.w, self.h)))


    def changeImage(self):
        name = str(self.pickImage().resolve())
        if name[-3:] == "png" or name[-3:] == "svg":
            self.setImage(name)
            self.setImagesource(name)
        else:
            print("No image picked, name is " + name)

    def setImagesource(self, name):
        self.imagesource = name

    def pickImage(self):
        return Path(QFileDialog.getOpenFileName(self.parent.parent(), filter="*.png *.svg")[0])

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
        # c2 = menu.addAction("Set group")
        # c2.triggered.connect(self.configGroup)

        c3 = menu.addAction("Set image")
        c3.triggered.connect(self.changeImage)

        if not self.isSet:
            c4 = menu.addAction("Add port")
            c4.triggered.connect(self.addPortDlg)

        # d1 = menu.addAction('Dump information')
        # d1.triggered.connect(self.dumpBlockInfo)
        #
        # e1 = menu.addAction('Inspect')
        # e1.triggered.connect(self.inspectBlock)

        menu.exec_(event.screenPos())

    def encode(self):
        if self.isVisible():
            print("Encoding a Generic Block")

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
            dct['Imagesource'] = self.imagesource
            dct['PortPairsNb'] = [self.getPairNb(i) for i in range(4)]

            dictName = "Block-"
            return dictName, dct

    def decode(self, i, resConnList, resBlockList):
        print("Portpair is " + str(i['PortPairsNb']))
        correcter = 0
        for j in range(4):
            if j == 2:
                correcter = -1
            for k in range(i['PortPairsNb'][j] + correcter):
                self.addPortPair(j)

        super(GenericBlock, self).decode(i, resConnList, resBlockList)
        self.setImage(i["Imagesource"])

    def decodePaste(self, i, offset_x, offset_y, resConnList, resBlockList, **kwargs):
        correcter = 0
        for j in range(4):
            if j == 2:
                correcter = -1
            for k in range(i['PortPairsNb'][j] + correcter):
                self.addPortPair(j)

        super(GenericBlock, self).decodePaste(i, offset_x, offset_y, resConnList, resBlockList)
        self.setImage(i["Imagesource"])

    def addPortPair(self, side):
        h = self.h
        w = self.w
        delta = 4
        print("side is " + str(side))
        self.inputs.append(PortItem("i", side, self))
        self.outputs.append(PortItem("o", side, self))
        # Allocate id
        self.childIds.append(self.parent.parent().idGen.getTrnsysID())

        portNb = [0, 0, 0, 0]
        for i in self.inputs:
            if i.side == 0:
                distBetweenPorts = (self.h - 4*delta) / (2 * self.getPairNb(0) - 1)
                print("distance betw ports " + str(distBetweenPorts))
                i.setPos(- 2*delta,
                          2 * delta + distBetweenPorts * portNb[0])
                portNb[0] += 1

                self.outputs[self.inputs.index(i)].setPos(- 2*delta,
                           2*delta + distBetweenPorts * portNb[0])
                portNb[0] += 1
            elif i.side == 1:
                distBetweenPorts = (self.w - 4 * delta) / (2 * self.getPairNb(1) - 1)
                i.setPos(2 * delta + distBetweenPorts * portNb[1], -2 * delta)
                portNb[1] += 1

                self.outputs[self.inputs.index(i)].setPos(2 * delta + distBetweenPorts * portNb[1], - 2 * delta)
                portNb[1] += 1

            elif i.side == 2:
                print("side == 2")
                distBetweenPorts = (self.h - 4 * delta) / (2 * self.getPairNb(2) - 1)
                print("side 2 dist betw ports is " + str(distBetweenPorts))
                i.setPos(2 * delta + w,
                         2 * delta + distBetweenPorts * portNb[2])
                print(2 * delta + distBetweenPorts * portNb[2])
                portNb[2] += 1

                self.outputs[self.inputs.index(i)].setPos(2 * delta + w,
                                                          2 * delta + distBetweenPorts * portNb[2])
                print(2 * delta + distBetweenPorts * portNb[2])
                portNb[2] += 1

            else:
                distBetweenPorts = (self.w - 4 * delta) / (2 * self.getPairNb(3) - 1)
                print("distance betw ports " + str(distBetweenPorts))
                i.setPos(2 * delta + distBetweenPorts * portNb[3], 2 * delta + h)
                portNb[3] += 1

                self.outputs[self.inputs.index(i)].setPos( 2 * delta + distBetweenPorts * portNb[3], 2 * delta + h)
                portNb[3] += 1

    def removePortPairOnSide(self, side):
        for i in self.inputs:
            if i.side == side:
                self.removePortPair(self.inputs.index(i))
                return

    def removePortPair(self, n):
        self.inputs.remove(self.inputs[n])
        self.outputs.remove(self.outputs[n])

    def updateFlipStateH(self, state):
        self.pixmap = QPixmap(self.image.mirrored(bool(state), self.flippedV))
        self.setPixmap(self.pixmap.scaled(QSize(self.w, self.h)))
        self.flippedH = bool(state)
        self.updatePortPos()

    def updateFlipStateV(self, state):
        self.pixmap = QPixmap(self.image.mirrored(self.flippedH, bool(state)))
        self.setPixmap(self.pixmap.scaled(QSize(self.w, self.h)))
        self.flippedV = bool(state)
        self.updatePortPos()

    # def exportBlackBox(self):
    #     resStr = ""
    #     for i in range(len(self.inputs)):
    #         resStr += "T" + self.displayName + "X" + str(i) + "=1 \n"
    #     eqNb = len(self.inputs)
    #     return resStr, eqNb

    def exportParametersFlowSolver(self, descConnLength):
        # descConnLength = 20
        equationNr = 0
        f = ''
        for i in range(len(self.inputs)):
            temp = ""
            c = self.inputs[i].connectionList[0]
            if hasattr(c.fromPort.parent, "heatExchangers") and self.inputs[i].connectionList.index(c) == 0:
                continue
            elif hasattr(c.toPort.parent, "heatExchangers") and self.inputs[i].connectionList.index(c) == 0:
                continue
            else:
                temp = str(c.trnsysId) + " " + str(
                    self.outputs[i].connectionList[0].trnsysId) + " 0 0 "  # + str(t.childIds[0])
                temp += " " * (descConnLength - len(temp))

                # Generic block will have a 2n-liner exportConnString
                self.exportConnsString += temp + "\n"
                f += temp + "!" + str(self.childIds[i]) + " : " + self.displayName + "X" + str(i) + "\n"

        return f, equationNr

    def exportInputsFlowSolver1(self):
        return "0,0 " * len(self.inputs), len(self.inputs)

    def exportInputsFlowSolver2(self):
        f = ""
        for i in range(len(self.inputs)):
            f += " " + str(self.exportInitialInput) + " "

        return f, len(self.inputs)

    def exportOutputsFlowSolver(self, prefix, abc, equationNumber, simulationUnit):
        tot = ""
        for j in range(len(self.inputs)):
            for i in range(0, 3):

                if i < 2:
                    temp = prefix + self.displayName + "-X" + str(j) + "_" + abc[i] + "=[" + str(simulationUnit) + "," + \
                           str(equationNumber) + "]\n"
                    tot += temp
                    self.exportEquations.append(temp)
                    # nEqUsed += 1  # DC
                equationNumber += 1  # DC-ERROR it should count anyway

        return tot, equationNumber, 2 * len(self.inputs)

    def getSubBlockOffset(self, c):
        for i in range(len(self.inputs)):
            if self.inputs[i] == c.toPort or self.inputs[i] == c.fromPort or self.outputs[i] == c.toPort or self.outputs[i] == c.fromPort:
                return i

    def addTree(self):
        """
        When a blockitem is added to the main window.
        A file explorer for that item is added to the right of the main window by calling this method
        """
        print(self.parent.parent())
        pathName = self.displayName
        if self.parent.parent().projectPath =='':
            # self.path = os.path.dirname(__file__)
            # self.path = os.path.join(self.path, 'default')
            self.path = self.parent.parent().projectFolder
            # now = datetime.now()
            # self.fileName = now.strftime("%Y%m%d%H%M%S")
            # self.path = os.path.join(self.path, self.fileName)
        else:
            self.path = self.parent.parent().projectPath
        self.path = os.path.join(self.path, 'ddck')
        self.path = os.path.join(self.path, pathName)
        if not os.path.exists(self.path):
            os.makedirs(self.path)

        self.model = MyQFileSystemModel()
        self.model.setRootPath(self.path)
        self.model.setName(self.displayName)
        self.tree = MyQTreeView(self.model, self)
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(self.path))
        self.tree.setObjectName("%sTree" % self.displayName)
        for i in range(1, self.model.columnCount()-1):
            self.tree.hideColumn(i)
        self.tree.setMinimumHeight(200)
        self.tree.setSortingEnabled(True)
        self.parent.parent().splitter.addWidget(self.tree)

    # def loadFile(self, file):
    #     filePath = self.parent.parent().projectPath
    #     msgB = QMessageBox()
    #     if filePath == '':
    #         msgB.setText("Please select a project path before loading!")
    #         msgB.exec_()
    #     else:
    #         print("file loaded into %s" % filePath)
    #         shutil.copy(file, filePath)

    def updateTreePath(self, path):
        """
        When the user chooses the project path for the file explorers, this method is called
        to update the root path.
        """
        pathName = self.displayName
        self.path = os.path.join(path, "ddck")
        self.path = os.path.join(self.path, pathName)
        if not os.path.exists(self.path):
            os.makedirs(self.path)
        self.model.setRootPath(self.path)
        self.tree.setRootIndex(self.model.index(self.path))

    def deleteBlock(self):
        """
                Overridden method to also delete folder
        """
        print("Block " + str(self) + " is deleting itself (" + self.displayName + ")")
        self.deleteConns()
        # print("self.parent.parent" + str(self.parent.parent()))
        self.parent.parent().trnsysObj.remove(self)
        print("deleting block " + str(self) + self.displayName)
        # print("self.scene is" + str(self.parent.scene()))
        self.parent.scene().removeItem(self)
        widgetToRemove = self.parent.parent().findChild(QTreeView, self.displayName+'Tree')
        shutil.rmtree(self.path)
        self.deleteLoadedFile()
        try:
            widgetToRemove.hide()
        except AttributeError:
            print("Widget doesnt exist!")
        else:
            print("Deleted widget")
        del self

    def setName(self, newName):
        """
        Overridden method to also change folder name
        """
        self.displayName = newName
        self.label.setPlainText(newName)
        self.model.setName(self.displayName)
        self.tree.setObjectName("%sTree" % self.displayName)
        print(os.path.dirname(self.path))
        # destPath = str(os.path.dirname(self.path))+'\\Generic_'+self.displayName
        destPath = os.path.join(os.path.split(self.path)[0],self.displayName)
        if os.path.exists(self.path):
            os.rename(self.path, destPath)
            self.path = destPath
            print(self.path)
