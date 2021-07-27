# pylint: skip-file
# type: ignore

import glob
import os
import shutil
import typing as _tp

from PyQt5.QtWidgets import QTreeView

from trnsysGUI.BlockItem import BlockItem
from trnsysGUI.MyQFileSystemModel import MyQFileSystemModel
from trnsysGUI.MyQTreeView import MyQTreeView
from trnsysGUI.PortItem import PortItem
import trnsysGUI.images as _img


class HeatPump(BlockItem):
    def __init__(self, trnsysType, parent, **kwargs):
        super().__init__(trnsysType, parent, **kwargs)

        self.inputs.append(PortItem("i", 0, self))
        self.inputs.append(PortItem("i", 2, self))
        self.outputs.append(PortItem("o", 0, self))
        self.outputs.append(PortItem("o", 2, self))
        self.loadedFiles = []

        # For restoring correct order of trnsysObj list
        self.childIds = []
        self.childIds.append(self.trnsysId)
        self.childIds.append(self.parent.parent().idGen.getTrnsysID())

        self.changeSize()
        self.addTree()

    def _getImageAccessor(self) -> _tp.Optional[_img.ImageAccessor]:
        return _img.HP_SVG

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

        self.origInputsPos = [[0, delta], [w, delta]]
        self.origOutputsPos = [[0, h - delta], [w, h - delta]]
        self.inputs[0].setPos(self.origInputsPos[0][0], self.origInputsPos[0][1])
        self.inputs[1].setPos(self.origInputsPos[1][0], self.origInputsPos[1][1])
        self.outputs[0].setPos(self.origOutputsPos[0][0], self.origOutputsPos[0][1])
        self.outputs[1].setPos(self.origOutputsPos[1][0], self.origOutputsPos[1][1])

        self.updateFlipStateH(self.flippedH)
        self.updateFlipStateV(self.flippedV)

        self.inputs[0].side = (self.rotationN + 2 * self.flippedH) % 4
        self.inputs[1].side = (self.rotationN + 2 - 2 * self.flippedH) % 4

        self.outputs[0].side = (self.rotationN + 2 * self.flippedH) % 4
        self.outputs[1].side = (self.rotationN + 2 - 2 * self.flippedH) % 4
        return w, h

    def encode(self):
        if self.isVisible():
            self.logger.debug("Encoding a HeatPump")

            # childIdList = []

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
            dct["PortsIDIn"] = portListInputs
            dct["PortsIDOut"] = portListOutputs
            dct["HeatPumpPosition"] = (float(self.pos().x()), float(self.pos().y()))
            dct["ID"] = self.id
            dct["trnsysID"] = self.trnsysId
            dct["childIds"] = self.childIds
            dct["FlippedH"] = self.flippedH
            dct["FlippedV"] = self.flippedH
            dct["RotationN"] = self.rotationN
            dct["GroupName"] = self.groupName

            dictName = "Block-"

            return dictName, dct

    def decode(self, i, resBlockList):
        self.logger.debug("Loading a HeatPump block")

        self.flippedH = i["FlippedH"]
        self.flippedV = i["FlippedV"]
        self.childIds = i["childIds"]
        self.displayName = i["BlockDisplayName"]
        self.changeSize()

        for x in range(len(self.inputs)):
            self.inputs[x].id = i["PortsIDIn"][x]
            self.logger.debug("Input at heatExchanger")

        for x in range(len(self.outputs)):
            self.outputs[x].id = i["PortsIDOut"][x]
            self.logger.debug("Output at heatExchanger")

        self.setPos(float(i["HeatPumpPosition"][0]), float(i["HeatPumpPosition"][1]))
        self.trnsysId = i["trnsysID"]
        self.id = i["ID"]

        self.groupName = "defaultGroup"
        self.setBlockToGroup(i["GroupName"])

        resBlockList.append(self)

    def decodePaste(self, i, offset_x, offset_y, resConnList, resBlockList, **kwargs):
        self.logger.debug("Loading a HeatPump in Decoder")

        self.changeSize()

        for x in range(len(self.inputs)):
            self.inputs[x].id = i["PortsIDIn"][x]
            self.logger.debug("Input at heatExchanger")

        for x in range(len(self.outputs)):
            self.outputs[x].id = i["PortsIDOut"][x]
            self.logger.debug("Output at heatExchanger")

        self.setPos(float(i["HeatPumpPosition"][0]) + offset_x, float(i["HeatPumpPosition"][1] + offset_y))
        self.groupName = "defaultGroup"
        self.setBlockToGroup(i["GroupName"])

        resBlockList.append(self)

    def exportBlackBox(self):
        equation = []
        files = glob.glob(os.path.join(self.path, "**/*.ddck"), recursive=True)
        if not (files):
            status = "noDdckFile"
            for i in range(1, 3):
                equation.append("T" + self.displayName + "X" + str(i) + "=1")
        else:
            status = "noDdckEntry"
        lines = []
        for file in files:
            infile = open(file, "r")
            lines += infile.readlines()
        for i in range(len(lines)):
            if "output" in lines[i].lower() and "to" in lines[i].lower() and "hydraulic" in lines[i].lower():
                counter = 1
                for j in range(i, len(lines) - i):
                    if lines[j][0] == "T":
                        outputT = lines[j].split("=")[0].replace(" ", "")
                        equation.append("T" + self.displayName + "X" + str(counter) + "=1 ! suggestion: " + outputT)
                        counter += 1
                    if counter == 3:
                        status = "success"
                        break
                break

        return status, equation

    def exportParametersFlowSolver(self, descConnLength):
        f = ""
        for i in range(len(self.inputs)):
            for c in self.inputs[i].connectionList:
                if len(self.outputs[i].connectionList) > 0:
                    if i == 0:
                        temp = (
                            str(c.trnsysId) + " " + str(self.outputs[i].connectionList[0].trnsysId) + " 0 0 "
                        )  # + str(t.childIds[0])
                        temp += " " * (descConnLength - len(temp))

                        # HeatPump will have a two-liner exportConnString
                        self.exportConnsString += temp + "\n"
                        f += temp + "!" + str(self.childIds[0]) + " : " + self.displayName + "HeatPump" + "\n"

                    elif i == 1:
                        temp = (
                            str(c.trnsysId) + " " + str(self.outputs[i].connectionList[0].trnsysId) + " 0 0 "
                        )  # + str(t.childIds[1])
                        temp += " " * (descConnLength - len(temp))

                        # HeatPump will have a two liner exportConnString
                        self.exportConnsString += temp + "\n"
                        f += temp + "!" + str(self.childIds[1]) + " : " + self.displayName + "Evap" + "\n"
                    else:
                        f += "Error: There are more inputs than trnsysIds" + "\n"

                    # Presumably used only for storing the order of connections
                    self.trnsysConn.append(c)
                    self.trnsysConn.append(self.outputs[i].connectionList[0])

                else:
                    f += "Output of HeatPump for input[{0}] is not connected ".format(i) + "\n"

        return f

    def exportInputsFlowSolver1(self):
        return "0,0 0,0 ", 2

    def exportInputsFlowSolver2(self):
        f = ""
        f += " " + str(self.exportInitialInput) + " " + str(self.exportInitialInput) + " "
        return f, 2

    def exportOutputsFlowSolver(self, prefix, abc, equationNumber, simulationUnit):
        tot = ""
        for j in range(2):
            for i in range(0, 3):

                if i < 2:
                    temp = (
                        prefix
                        + self.displayName
                        + "-Hp-Side"
                        + str(j)
                        + "_"
                        + abc[i]
                        + "=["
                        + str(simulationUnit)
                        + ","
                        + str(equationNumber)
                        + "]\n"
                    )
                    tot += temp
                    self.exportEquations.append(temp)
                    # nEqUsed += 1  # DC
                equationNumber += 1  # DC-ERROR it should count anyway

        return tot, equationNumber, 4

    def getSubBlockOffset(self, c):
        for i in range(2):
            if (
                self.inputs[i] == c.toPort
                or self.inputs[i] == c.fromPort
                or self.outputs[i] == c.toPort
                or self.outputs[i] == c.fromPort
            ):
                return i

    def addTree(self):
        """
        When a blockitem is added to the main window.
        A file explorer for that item is added to the right of the main window by calling this method
        """
        self.logger.debug(self.parent.parent())
        pathName = self.displayName
        if self.parent.parent().projectPath == "":
            # self.path = os.path.dirname(__file__)
            # self.path = os.path.join(self.path, 'default')
            self.path = self.parent.parent().projectFolder
            # now = datetime.now()
            # self.fileName = now.strftime("%Y%m%d%H%M%S")
            # self.path = os.path.join(self.path, self.fileName)
        else:
            self.path = self.parent.parent().projectPath
        self.path = os.path.join(self.path, "ddck")
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
        for i in range(1, self.model.columnCount() - 1):
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
    #         self.logger.debug("file loaded into %s" % filePath)
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
        self.logger.debug("Block " + str(self) + " is deleting itself (" + self.displayName + ")")
        self.deleteConns()
        # self.logger.debug("self.parent.parent" + str(self.parent.parent()))
        self.parent.parent().trnsysObj.remove(self)
        self.logger.debug("deleting block " + str(self) + self.displayName)
        # self.logger.debug("self.scene is" + str(self.parent.scene()))
        self.parent.scene().removeItem(self)
        widgetToRemove = self.parent.parent().findChild(QTreeView, self.displayName + "Tree")
        shutil.rmtree(self.path)
        self.deleteLoadedFile()
        try:
            widgetToRemove.hide()
        except AttributeError:
            self.logger.debug("Widget doesnt exist!")
        else:
            self.logger.debug("Deleted widget")
        del self

    def setName(self, newName):
        """
        Overridden method to also change folder name
        """
        self.displayName = newName
        self.label.setPlainText(newName)
        self.model.setName(self.displayName)
        self.tree.setObjectName("%sTree" % self.displayName)
        self.logger.debug(os.path.dirname(self.path))
        # destPath = str(os.path.dirname(self.path))+'\\HP_'+self.displayName
        destPath = os.path.join(os.path.split(self.path)[0], self.displayName)
        if os.path.exists(self.path):
            os.rename(self.path, destPath)
            self.path = destPath
            self.logger.debug(self.path)
