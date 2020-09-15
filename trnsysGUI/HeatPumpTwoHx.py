import os
import shutil

from PyQt5.QtCore import QSize
from PyQt5.QtGui import QPixmap, QTransform
from PyQt5.QtWidgets import QTreeView

from trnsysGUI.BlockItem import BlockItem
from trnsysGUI.MyQFileSystemModel import MyQFileSystemModel
from trnsysGUI.MyQTreeView import MyQTreeView
from trnsysGUI.PortItem import PortItem


class HeatPumpTwoHx(BlockItem):
    def __init__(self, trnsysType, parent, **kwargs):
        super(HeatPumpTwoHx, self).__init__(trnsysType, parent, **kwargs)

        self.inputs.append(PortItem('i', 0, self))
        self.inputs.append(PortItem('i', 2, self))
        self.inputs.append(PortItem('i', 2, self))

        self.outputs.append(PortItem('o', 0, self))
        self.outputs.append(PortItem('o', 2, self))
        self.outputs.append(PortItem('o', 2, self))
        self.loadedFiles = []

        self.pixmap = QPixmap(self.image)
        self.setPixmap(self.pixmap.scaled(QSize(self.w, self.h)))

        # For restoring correct order of trnsysObj list
        self.childIds = []
        self.childIds.append(self.trnsysId)
        self.childIds.append(self.parent.parent().idGen.getTrnsysID())
        self.childIds.append(self.parent.parent().idGen.getTrnsysID())

        self.subBlockCounter = 0

        self.changeSize()
        self.addTree()

    def changeSize(self):
        w = self.w
        h = self.h

        """ Resize block function """
        delta = 20

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

        self.inputs[0].setPos(0,delta)
        self.inputs[1].setPos(w,delta)
        self.inputs[2].setPos(w,h-2*delta)
        # self.inputs[0].side = 0 + 2 * self.flippedH
        # self.inputs[1].side = 2 - 2 * self.flippedH
        # self.inputs[2].side = 2 - 2 * self.flippedH  0.4 * h - 0.4 * h * self.flippedV + 0.6 * h * self.flippedV
        self.inputs[0].side = (self.rotationN + 2 * self.flippedH) % 4
        self.inputs[1].side = (self.rotationN + 2 - 2 * self.flippedH) % 4
        self.inputs[2].side = (self.rotationN + 2 - 2 * self.flippedH) % 4

        self.outputs[0].setPos(0,h-delta)
        self.outputs[1].setPos(w,2*delta)
        self.outputs[2].setPos(w,h-delta)
        # self.outputs[0].side = 0 + 2 * self.flippedH
        # self.outputs[1].side = 2 - 2 * self.flippedH
        # self.outputs[2].side = 2 - 2 * self.flippedH
        self.outputs[0].side = (self.rotationN + 2 * self.flippedH) % 4
        self.outputs[1].side = (self.rotationN + 2 - 2 * self.flippedH) % 4
        self.outputs[2].side = (self.rotationN + 2 - 2 * self.flippedH) % 4
        return w, h

    def encode(self):
        if self.isVisible():
            print("Encoding a HeatPump")

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
            dct['PortsIDIn'] = portListInputs
            dct['PortsIDOut'] = portListOutputs
            dct['HeatPumpPosition'] = (float(self.pos().x()), float(self.pos().y()))
            dct['ID'] = self.id
            dct['trnsysID'] = self.trnsysId
            dct['childIds'] = self.childIds
            dct['FlippedH'] = self.flippedH
            dct['FlippedV'] = self.flippedH
            dct['RotationN'] = self.rotationN
            dct['GroupName'] = self.groupName

            dictName = "Block-"

            return dictName, dct

    def decode(self, i, resConnList, resBlockList):
        self.flippedH = i["FlippedH"]
        self.flippedV = i["FlippedV"]
        self.childIds = i["childIds"]
        self.displayName = i["BlockDisplayName"]
        self.changeSize()

        for x in range(len(self.inputs)):
            self.inputs[x].id = i["PortsIDIn"][x]
            print("Input at heatExchanger")

        for x in range(len(self.outputs)):
            self.outputs[x].id = i["PortsIDOut"][x]
            print("Output at heatExchanger")

        self.setPos(float(i["HeatPumpPosition"][0]), float(i["HeatPumpPosition"][1]))
        self.trnsysId = i["trnsysID"]
        self.id = i["ID"]

        self.groupName = "defaultGroup"
        self.setBlockToGroup(i["GroupName"])

        resBlockList.append(self)

    def decodePaste(self, i, offset_x, offset_y, resConnList, resBlockList, **kwargs):
        self.flippedH = i["FlippedH"]
        self.flippedV = i["FlippedV"]

        self.changeSize()

        for x in range(len(self.inputs)):
            self.inputs[x].id = i["PortsIDIn"][x]
            print("Input at heatExchanger")

        for x in range(len(self.outputs)):
            self.outputs[x].id = i["PortsIDOut"][x]
            print("Output at heatExchanger")

        self.setPos(float(i["HeatPumpPosition"][0] + offset_x), float(i["HeatPumpPosition"][1] + offset_y))
        # self.trnsysId = i["trnsysID"]
        # self.id = i["ID"]

        self.groupName = "defaultGroup"
        self.setBlockToGroup(i["GroupName"])
        resBlockList.append(self)

    def exportBlackBox(self):
        resStr = "T" + self.displayName + "X0" + "=1 \n"
        resStr += "T" + self.displayName + "X1" + "=1 \n"
        resStr += "T" + self.displayName + "X2" + "=1 \n"
        eqNb = 3
        return resStr, eqNb

    def exportParametersFlowSolver(self, descConnLength):
        # descConnLength = 20
        f = ""
        for i in range(len(self.inputs)):
            # ConnectionList lenght should be max offset
            temp = ""
            for c in self.inputs[i].connectionList:
                if hasattr(c.fromPort.parent, "heatExchangers") and self.inputs[i].connectionList.index(c) == 0:
                    continue
                elif hasattr(c.toPort.parent, "heatExchangers") and self.inputs[i].connectionList.index(c) == 0:
                    continue
                else:
                    if len(self.outputs[i].connectionList) > 0:
                        #HeatPumpTwoHx exportConnsString has 3 lines
                        if i == 0:
                            temp = str(c.trnsysId) + " " + str(
                                self.outputs[i].connectionList[0].trnsysId) + " 0 0 "  # + str(t.childIds[0])
                            temp += " " * (descConnLength - len(temp))

                            self.exportConnsString += temp + "\n"
                            f += temp + "!" + str(self.childIds[0]) + " : " + self.displayName + "Side1" + "\n"

                        elif i == 1:
                            temp = str(c.trnsysId) + " " + str(
                                self.outputs[i].connectionList[0].trnsysId) + " 0 0 "  # + str(t.childIds[1])
                            temp += " " * (descConnLength - len(temp))

                            self.exportConnsString += temp + "\n"
                            f += temp + "!" + str(self.childIds[1]) + " : " + self.displayName + "Side2" + "\n"

                        elif i == 2:
                            temp = str(c.trnsysId) + " " + str(
                                self.outputs[i].connectionList[0].trnsysId) + " 0 0 "  # + str(t.childIds[1])
                            temp += " " * (descConnLength - len(temp))

                            self.exportConnsString += temp + "\n"
                            f += temp + "!" + str(self.childIds[2]) + " : " + self.displayName + "Side3" + "\n"
                        else:
                            f += "Error: There are more inputs than trnsysIds" + "\n"

                        # Presumably used only for storing the order of connections
                        self.trnsysConn.append(c)
                        self.trnsysConn.append(self.outputs[i].connectionList[0])

                    else:
                        f += "Output of ExternalHx for input[{0}] is not connected ".format(i) + "\n"

        return f, 2

    def exportInputsFlowSolver1(self):
        return "0,0 0,0 0,0", 3

    def exportInputsFlowSolver2(self):
        f = ""
        f += " " + str(self.exportInitialInput) + " " + str(self.exportInitialInput) + " " + str(self.exportInitialInput) + " "
        return f, 3

    def exportOutputsFlowSolver(self, prefix, abc, equationNumber, simulationUnit):
        tot = ""
        for j in range(3):
            for i in range(0, 3):
                if i < 2:
                    temp = prefix + self.displayName + "-Side" + str(j) + "_" + abc[i] + "=[" + str(simulationUnit) + "," + \
                           str(equationNumber) + "]\n"
                    tot += temp
                    self.exportEquations.append(temp)
                    # nEqUsed += 1  # DC
                equationNumber += 1  # DC-ERROR it should count anyway

        return tot, equationNumber, 6

    def getSubBlockOffset(self, c):
        for i in range(3):
            if self.inputs[i] == c.toPort or self.inputs[i] == c.fromPort or self.outputs[i] == c.toPort or self.outputs[i] == c.fromPort:
                return i

    def addTree(self):
        """
        When a blockitem is added to the main window.
        A file explorer for that item is added to the right of the main window by calling this method
        """
        print(self.parent.parent())
        pathName = 'HPTwoHx_' + self.displayName
        if self.parent.parent().projectPath =='':
            # self.path = os.path.dirname(__file__)
            # self.path = os.path.join(self.path, 'default')
            self.path = self.parent.parent().tempPath
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
        pathName = 'HPTwoHx_' + self.displayName
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
        destPath = str(os.path.dirname(self.path))+'\\HPTwoHx_'+self.displayName
        if os.path.exists(self.path):
            os.rename(self.path, destPath)
            self.path = destPath
            print(self.path)
