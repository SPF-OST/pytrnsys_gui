# pylint: skip-file
# type: ignore

import os
import random
import shutil
import typing as _tp

from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QMenu, QMessageBox, QTreeView

import trnsysGUI.images as _img
import trnsysGUI.storageTank.model as _model
from trnsysGUI.BlockItem import BlockItem
from trnsysGUI.ConfigureStorageDialog import ConfigureStorageDialog
from trnsysGUI.Connection import Connection
from trnsysGUI.Connector import Connector
from trnsysGUI.directPortPair import DirectPortPair
from trnsysGUI.HeatExchanger import HeatExchanger
from trnsysGUI.MyQFileSystemModel import MyQFileSystemModel
from trnsysGUI.MyQTreeView import MyQTreeView
from trnsysGUI.PortItem import PortItem
from trnsysGUI.TeePiece import TeePiece
from trnsysGUI.type1924.createType1924 import Type1924_TesPlugFlow


class StorageTank(BlockItem):
    def __init__(self, trnsysType, parent, **kwargs):
        super(StorageTank, self).__init__(trnsysType, parent, **kwargs)

        self.parent = parent
        self.dckFilePath = ""

        self.directPortPairs: _tp.List[DirectPortPair] = []

        self.heatExchangers: _tp.List[HeatExchanger] = []

        self.childIds = []
        self.childIds.append(self.trnsysId)

        # List containing all the conns and blocks inside, used to input into connInside()
        self.insideConnLeft = []
        self.insideConnRight = []

        self.hxInsideConnsLeft = []
        self.hxInsideConnsRight = []

        self.blackBoxEquations = []

        self.nTes = self.parent.parent().idGen.getStoragenTes()
        self.storageType = self.parent.parent().idGen.getStorageType()

        self.changeSize()
        self.addTree()

    @property
    def leftDirectPortPairsPortItems(self):
        return self._getDirectPortPairPortItems(isOnLeftSide=True)

    @property
    def rightDirectPortPairsPortItems(self):
        return self._getDirectPortPairPortItems(isOnLeftSide=False)

    def _getDirectPortPairPortItems(self, isOnLeftSide: bool):
        return [
            p
            for dpp in self.directPortPairs
            if dpp.isOnLeftSide == isOnLeftSide
            for p in [dpp.fromPort, dpp.toPort]
        ]

    def _getImageAccessor(self) -> _tp.Optional[_img.ImageAccessor]:
        return _img.STORAGE_TANK_SVG

    # Setter functions
    def setParent(self, p):
        self.logger.debug("Setting parent of Storage Tank (and its hx)")
        self.parent = p

        if self not in self.parent.parent().trnsysObj:
            self.parent.parent().trnsysObj.append(self)

        # TODO: Should hx be also in trnsysObj?
        for hx in self.heatExchangers:
            hx.parent = self

    def addDirectPortPair(
        self,
        isOnLeftSide,
        relativeInputHeight,
        relativeOutputHeight,
        storageTankHeight,
        **kwargs,
    ):
        sideNr = 0 if isOnLeftSide else 2

        port1 = PortItem("i", sideNr, self)
        port1.setZValue(100)

        port2 = PortItem("o", sideNr, self)
        port2.setZValue(100)

        self.childIds.append(self.parent.parent().idGen.getTrnsysID())

        x = 0 if isOnLeftSide else self.w
        inputY = storageTankHeight - relativeInputHeight * storageTankHeight
        outputY = storageTankHeight - relativeOutputHeight * storageTankHeight

        port1.setPos(x, inputY)
        port2.setPos(x, outputY)

        side = 0 if isOnLeftSide else 2
        port1.side = side
        port2.side = side

        randomInt = int(random.uniform(20, 200))
        randomColor = QColor(randomInt, randomInt, randomInt)

        port1.innerCircle.setBrush(randomColor)
        port2.innerCircle.setBrush(randomColor)
        port1.visibleColor = randomColor
        port2.visibleColor = randomColor

        directPortPair = self._createDirectPortPair(
            isOnLeftSide,
            port1,
            port2,
            relativeInputHeight,
            relativeOutputHeight,
            kwargs,
        )

        self.directPortPairs.append(directPortPair)
        self.inputs.append(directPortPair.fromPort)
        self.outputs.append(directPortPair.toPort)

    @staticmethod
    def _createDirectPortPair(
        isOnLeftSide,
        port1,
        port2,
        relativeInputHeight,
        relativeOutputHeight,
        kwargs,
    ):
        # Misuse of kwargs for detecting if the manual port pair is being loaded and not newly created
        if not kwargs:
            directPortPair = DirectPortPair(
                "<TODO: is this needed>",  # TODO@dbi remove virtual connections
                port1,
                port2,
                relativeInputHeight,
                relativeOutputHeight,
                isOnLeftSide
            )
            return directPortPair

        port1.id = kwargs["fromPortId"]
        port2.id = kwargs["toPortId"]

        name = kwargs["connDispName"]
        directPortPair = DirectPortPair(
            name,
            port1,
            port2,
            relativeInputHeight,
            relativeOutputHeight,
            isOnLeftSide
        )

        return directPortPair

    def checkConnectInside(self, port1, port2, maxhops, d):
        """
        Was used to check if connectInside works
        Basically a depth first algorithm
        Parameters
        ----------
        port1
        port2
        maxhops
        d

        Returns
        -------

        """
        port1.visited = True

        self.logger.debug(" " * 3 * d + "In port1 " + str(port1) + "at depth " + str(d))
        self.logger.debug(
            " " * 3 * d + "Connection list is " + str(port1.connectionList)
        )
        self.logger.debug(" " * 3 * d + "Parent is " + str(port1.parent))

        if port1 is port2:
            self.logger.debug(
                " " * 3 * d + "Found a connection between port 1 and port 2"
            )

        if d == maxhops:
            self.logger.debug(" " * 3 * d + "Port + " + str(port1) + " is returning.")
            return

        if port1.parent.name == "TeePiece.png":
            # self.logger.debug("We are at T piece " + str(port1.parent))
            conns = port1.parent.getConnections()
            # self.logger.debug("Connections of T piece are " + str(conns))
            for c in conns:
                self.logger.debug(" " * 3 * d + "Conns")
                if c.fromPort.parent is port1.parent:
                    if (not c.fromPort.visited) and (not c.toPort.visited):
                        c.fromPort.visited = True
                        self.checkConnectInside(c.toPort, port2, maxhops, d + 1)

                if c.toPort.parent is port1.parent:
                    if (not c.toPort.visited) and (not c.fromPort.visited):
                        c.toPort.visited = True
                        self.checkConnectInside(c.fromPort, port2, maxhops, d + 1)

        if port1.parent.name == "StorageTank":
            # self.logger.debug("We are at " + str(port1.parent))

            if d > 1:
                self.logger.debug(
                    " " * 3 * d
                    + "port1 "
                    + str(port1)
                    + " at StorageTank is returning."
                )
                return

            for j in port1.connectionList:
                if j.toPort is port1:
                    self.logger.debug(" " * 3 * d + "toPort is port1 is " + str(port1))
                    self.logger.debug(
                        " " * 3 * d + "fromPort is " + str(j.fromPort) + "\n"
                    )
                    if not j.fromPort.visited:
                        self.checkConnectInside(j.fromPort, port2, maxhops, d + 1)
                    else:
                        self.logger.debug(
                            " " * 3 * d
                            + "Port was already visited, at depth "
                            + str(d)
                            + " at Storage Tank"
                        )
                if j.fromPort is port1:
                    self.logger.debug(" " * 3 * d + "fromPort is port1" + str(port1))
                    self.logger.debug(" " * 3 * d + "toPort is " + str(j.toPort) + "\n")
                    if not j.toPort.visited:
                        self.checkConnectInside(j.toPort, port2, maxhops, d + 1)
                    else:
                        self.logger.debug(
                            " " * 3 * d
                            + "Port was already visited, at depth "
                            + str(d)
                            + " at Storage Tank"
                        )

    def connectInside(self, connectedExternalPorts, storageTankPorts, teePieces, side):
        tempArrConn = []

        connectedExternalPortsCopy = connectedExternalPorts

        # Assert that the storage has at least 2 ports at side
        if len(connectedExternalPorts) < 2:
            self.logger.error("storage needs at least 2 ports on a side")
            return

        if len(connectedExternalPorts) == 2:

            connector = Connector("Connector", self.parent)
            connector.displayName = (
                "Conn" + self.displayName + side + str(connector.id)
            )

            # Used for recognizing it to print the temperature of the storage ports
            connector.inFirstRow = True
            connector.setVisible(False)

            self.parent.scene().addItem(connector)
            teePieces.append(connector)

            firstConnectedExternalPort = connectedExternalPorts[0]
            c1 = self._createConnectionBetweenExternalPortAndConnector(connector, firstConnectedExternalPort)

            secondConnectedExternalPort = connectedExternalPorts[1]
            c2 = self._createConnectionBetweenExternalPortAndConnector(connector, secondConnectedExternalPort)

            c1.displayName = firstConnectedExternalPort.connectionList[0].displayName
            c1.isStorageIO = True
            c2.displayName = secondConnectedExternalPort.connectionList[0].displayName
            c2.isStorageIO = True
            return

        h = 20
        # self.logger.debug("Self.parent.parent()" + str(self.parent.parent()))
        layer = 1
        while len(connectedExternalPorts) > 2:
            mem = []
            if len(connectedExternalPorts) % 2 == 0:
                x = len(connectedExternalPorts)
                self.logger.debug("Even number of ports in side")
            else:
                x = len(connectedExternalPorts) - 1
                mem.append(connectedExternalPorts[x])
                # self.logger.debug("Uneven " + side(x))

            for i in range(0, x, 2):
                tpiece = TeePiece("TeePiece", self.parent)
                tpiece.displayName = (
                    "TeeTes" + self.displayName + side + str(tpiece.id)
                )
                tpiece.setVisible(False)
                self.parent.scene().addItem(tpiece)
                teePieces.append(tpiece)

                c1 = Connection(connectedExternalPorts[i], tpiece.inputs[0], True, self.parent.parent())
                c2 = Connection(
                    tpiece.inputs[1], connectedExternalPorts[i + 1], True, self.parent.parent()
                )
                self.logger.debug(
                    "c1 is from "
                    + connectedExternalPorts[i].parent.displayName
                    + " to "
                    + tpiece.inputs[0].parent.displayName
                )
                self.logger.debug(
                    "c2 is from "
                    + tpiece.inputs[1].parent.displayName
                    + " to "
                    + connectedExternalPorts[i + 1].parent.displayName
                )
                if layer > 1:
                    c1.firstS.setVisible(False)
                    c2.firstS.setVisible(False)
                    c1.hiddenGenerated = True
                    c2.hiddenGenerated = True

                resId = ""
                for j in c1.displayName:
                    if j.isdigit():
                        resId += str(j)

                # self.logger.debug("c1 name before is " + c1.displayName)
                c1.displayName = "PiTes" + side + self.displayName + "_" + resId
                # self.logger.debug("c1 name is " + c1.displayName)

                resId = ""

                for j in c2.displayName:
                    if j.isdigit():
                        resId += str(j)

                c2.displayName = "PiTes" + side + self.displayName + "_" + resId

                tempArrConn.append(c1)
                tempArrConn.append(c2)

                # self.parent.addItem(QGraphicsEllipseItem(h, i * 10, 3, 3))

                if i == 0:
                    mem.insert(0, tpiece.outputs[0])
                else:
                    mem.insert(-1, tpiece.outputs[0])

            connectedExternalPorts = mem
            layer += 1
            h += 20
            # self.logger.debug(str(len(side)))

        lastC = Connection(connectedExternalPorts[0], connectedExternalPorts[1], True, self.parent.parent())
        lastC.firstS.setVisible(False)
        self.logger.debug(
            "lastc is from "
            + connectedExternalPorts[0].parent.displayName
            + " to "
            + connectedExternalPorts[1].parent.displayName
        )
        resId = ""
        for j in lastC.displayName:
            if j.isdigit():
                resId += str(j)
        lastC.displayName = "PiTes" + side + self.displayName + "_" + resId

        if len(storageTankPorts) > 2:
            lastC.hiddenGenerated = True

        # Here the virtual pipes clone the name of their corresponding real pipe
        # Could be used to set a new attribute generatedPrinted
        for s in connectedExternalPortsCopy:
            for t in tempArrConn:
                if t.fromPort is s or t.toPort is s:
                    self.logger.debug("This is a real connection " + str(t.displayName))
                    if len(s.connectionList) > 0:
                        t.displayName = s.connectionList[0].displayName  # + "GEN"
                        t.setClone(True)
                    else:
                        self.logger.debug(
                            "Found a port outside that has no connection to inside"
                        )

        # If tpieces were generated, the first len(connectedExternalPortsCopy) ones have to be marked as firstRow
        for x in teePieces[: len(connectedExternalPortsCopy)]:
            x.inFirstRow = True

    def _createConnectionBetweenExternalPortAndConnector(self, connector, connectedExternalPort):
        if self._isSourcePort(connectedExternalPort):
            return Connection(
                connectedExternalPort, connector.inputs[0], True, self.parent.parent()
            )
        else:
            return Connection(
                connector.inputs[0], connectedExternalPort, True, self.parent.parent()
            )

    @staticmethod
    def _isSourcePort(port):
        return port.connectionList[0].fromPort is port

    def connectHxs(self, outsidePorts, connectors, heatX):
        firstConnectedExternalPort = outsidePorts[0]
        secondConnectedExternalPort = outsidePorts[1]
        self.logger.debug("ports have " + str(firstConnectedExternalPort.parent) + str(secondConnectedExternalPort.parent))

        connector = Connector("Connector", self.parent)
        connector.displayName = heatX.displayName

        c1 = self._createConnectionBetweenExternalPortAndConnector(connector, firstConnectedExternalPort)
        c2 = self._createConnectionBetweenExternalPortAndConnector(connector, secondConnectedExternalPort)

        connectors.append(connector)
        c1.displayName = firstConnectedExternalPort.connectionList[0].displayName
        c1.isStorageIO = True
        c2.displayName = secondConnectedExternalPort.connectionList[0].displayName
        c2.isStorageIO = True

    # Transform related
    def changeSize(self):
        """ Resize block function """
        w = self.w
        h = self.h

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

        return w, h

    def updateImage(self):
        super().updateImage()
        self.label.setPos(self.label.pos().x(), self.h)

    def updatePortItemPositions(self, deltaH, deltaW):
        for p in self.inputs + self.outputs:
            rel_h_old = p.pos().y() / self.h
            if p.side == 0:
                p.setPos(p.pos().x(), rel_h_old * (self.h + deltaH))
            else:
                p.setPos(p.pos().x() + deltaW, rel_h_old * (self.h + deltaH))

    def updateHeatExchangersAfterTankSizeChange(self):
        for hx in self.heatExchangers:
            hx.setTankSize(self.w, self.h)

    def encode(self):
        if not self.isVisible():
            raise RuntimeError("Cannot encode an invisible storage tank.")

        heatExchangerModels = self._getHeatExchangerModelsForSerialization()
        portPairModels = self._getDirectPortPairModelsForEncode()
        position = float(self.pos().x()), float(self.pos().y())

        storageTankModel = _model.StorageTank(
            self.flippedH,
            self.flippedV,
            self.name,
            self.displayName,
            self.groupName,
            self.id,
            self.trnsysId,
            self.h,
            position,
            heatExchangerModels,
            portPairModels
        )

        dictName = "Block-"
        return dictName, storageTankModel.to_dict()

    def _getDirectPortPairModelsForEncode(self):
        portPairModels = []
        for directPort in self.directPortPairs:
            side = _model.Side.createFromSideNr(directPort.fromPort.side)

            inputPortModel = _model.Port(
                directPort.fromPort.id, directPort.relativeInputHeight
            )

            outputPortModel = _model.Port(
                directPort.toPort.id, directPort.relativeOutputHeight
            )

            portPairModel = _model.PortPair(
                side, directPort.name, inputPortModel, outputPortModel
            )

            directPortPairModel = _model.DirectPortPair(portPairModel)

            portPairModels.append(directPortPairModel)

        return portPairModels

    def _getHeatExchangerModelsForSerialization(self):
        heatExchangerModels = []
        for heatExchanger in self.heatExchangers:
            side = _model.Side.createFromSideNr(heatExchanger.sSide)

            inputPort = _model.Port(
                heatExchanger.port1.id,
                heatExchanger.relativeInputHeight,
            )

            outputPort = _model.Port(
                heatExchanger.port2.id,
                heatExchanger.relativeOutputHeight,
            )

            portPair = _model.PortPair(
                side, heatExchanger.displayName, inputPort, outputPort
            )

            heatExchangerModel = _model.HeatExchanger(
                portPair,
                heatExchanger.w,
                heatExchanger.parent.id,
                heatExchanger.id,
            )

            heatExchangerModels.append(heatExchangerModel)

        return heatExchangerModels

    @staticmethod
    def _getConnectionsAmong(ports: _tp.Sequence[PortItem]) -> _tp.Sequence[Connection]:
        return [
            c
            for fromPort in ports
            for c in fromPort.connectionList
            if c.fromPort is fromPort and c.toPort in ports
        ]

    def decode(self, i, resBlockList):
        offset_x = 0
        offset_y = 0
        self._decodeInternal(
            i, offset_x, offset_y, resBlockList, shallSetNamesAndIDs=True
        )

    def _decodeInternal(
        self,
        i,
        offset_x,
        offset_y,
        resBlockList,
        shallSetNamesAndIDs: bool,
    ):
        self.logger.debug("Loading a Storage in Decoder")

        model = _model.StorageTank.from_dict(i)

        self.flippedH = model.isHorizontallyFlipped

        if shallSetNamesAndIDs:
            self.displayName = model.BlockDisplayName

        self.changeSize()
        self.h = model.height
        self.updateImage()

        self.setPos(model.position[0] + offset_x, model.position[1] + offset_y)

        if shallSetNamesAndIDs:
            self.trnsysId = model.trnsysId
            self.id = model.id
            self.groupName = "defaultGroup"
            self.setBlockToGroup(model.groupName)

        for heatExchangerModel in model.heatExchangers:
            self._decodeHeatExchanger(heatExchangerModel, shallSetNamesAndIDs)

        for portPairModel in model.directPortPairs:
            self._decodeDirectPortPair(portPairModel, shallSetNamesAndIDs)

        resBlockList.append(self)

    def _decodeDirectPortPair(
        self,
        portPairModel: _model.DirectPortPair,
        shallSetNamesAndIDs: bool,
    ) -> DirectPortPair:
        portPair = portPairModel.portPair

        name = portPair.name if shallSetNamesAndIDs else portPair.name + "New"

        self.addDirectPortPair(
            isOnLeftSide=portPair.side == _model.Side.LEFT,
            relativeInputHeight=portPair.inputPort.relativeHeight,
            relativeOutputHeight=portPair.outputPort.relativeHeight,
            storageTankHeight=self.h,
            fromPortId=portPair.inputPort.id,
            toPortId=portPair.outputPort.id,
            connDispName=name,
            loadedConn=True,
        )

    def _decodeHeatExchanger(
        self, heatExchangerModel: _model.HeatExchanger, shallSetNamesAndIDs: bool
    ):
        portPair = heatExchangerModel.portPair

        sideNr = portPair.side.toSideNr()

        name = portPair.name if shallSetNamesAndIDs else portPair.name + "New"

        heatExchanger = HeatExchanger(
            sideNr,
            heatExchangerModel.width,
            portPair.inputPort.relativeHeight,
            portPair.outputPort.relativeHeight,
            self.w,
            self.h,
            self,
            name,
            loadedHx=True,
        )

        if shallSetNamesAndIDs:
            heatExchanger.setId(heatExchangerModel.id)

        heatExchanger.port1.id = portPair.inputPort.id
        heatExchanger.port2.id = portPair.outputPort.id

    def decodePaste(self, i, offset_x, offset_y, resConnList, resBlockList, **kwargs):
        self._decodeInternal(
            i, offset_x, offset_y, resBlockList, resConnList, shallSetNamesAndIDs=False
        )

    # Debug
    def dumpBlockInfo(self):
        self.logger.debug("storage input list " + str(self.inputs))
        self.logger.debug("storage outputs list " + str(self.outputs))
        self.logger.debug("storage leftside " + str(self.leftDirectPortPairsPortItems))
        self.logger.debug(
            "storage rightside " + str(self.rightDirectPortPairsPortItems)
        )
        self.parent.parent().dumpInformation()

    def deleteBlockDebug(self):
        self.logger.debug("Listing all connections")
        conns = []
        for p in self.inputs + self.outputs:
            for c in p.connectionList:
                conns.append(c)

        [
            self.logger.debug(
                c.displayName
                + ", fromPort: "
                + c.fromPort.parent.displayName
                + ", toPort: "
                + c.toPort.parent.displayName
            )
            for c in conns
        ]

    def printPortNb(self):
        self.logger.debug("ST has " + str(self.inputs) + " and " + str(self.outputs))

    # Misc
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

        e3 = menu.addAction("Export ddck")
        e3.triggered.connect(self.exportDck)

        menu.exec_(event.screenPos())

    def mouseDoubleClickEvent(self, event):
        self.dia = ConfigureStorageDialog(self, self.scene().parent())

    def hasManPortById(self, idFind):

        res = -1

        for p in self.leftDirectPortPairsPortItems:
            if p.id == idFind:
                res = True

        for p in self.rightDirectPortPairsPortItems:
            if p.id == idFind:
                res = False
        return res

    # Export related
    def exportBlackBox(self):
        equations = []
        ddcxPath = os.path.join(self.path, self.displayName)
        ddcxPath = ddcxPath + ".ddcx"
        self.exportDck()
        if os.path.isfile(ddcxPath):
            infile = open(ddcxPath, "r")
            lines = infile.readlines()
            for line in lines:
                if line[0] == "T":
                    equations.append(line.replace("\n", ""))
            return "success", equations
        else:
            self.logger.warning("No file at " + ddcxPath)
            return "noDdckFile", equations

    def exportParametersFlowSolver(self, descConnLength):
        return "", 0

    def exportInputsFlowSolver1(self):
        return "", 0

    def exportInputsFlowSolver2(self):
        return self.exportInputsFlowSolver1()

    def exportOutputsFlowSolver(self, prefix, abc, equationNumber, simulationUnit):
        return "", equationNumber, 0

    def exportDck(self):

        if not self.checkConnExists():
            msgb = QMessageBox()
            msgb.setText("Please connect all ports before exporting!")
            msgb.exec_()
            return
        noError = self.debugConn()

        if not noError:
            qmb = QMessageBox()
            qmb.setText("Ignore connection errors and continue with export?")
            qmb.setStandardButtons(QMessageBox.Save | QMessageBox.Cancel)
            qmb.setDefaultButton(QMessageBox.Cancel)
            ret = qmb.exec()
            if ret == QMessageBox.Save:
                self.logger.debug("Overwriting")
                # continue
            else:
                self.logger.debug("Canceling")
                return

        nPorts = len(self.directPortPairs)
        nHx = len(self.heatExchangers)

        self.logger.debug("Storage Type: " + str(self.storageType))
        self.logger.debug("nTes: " + str(self.nTes))
        self.logger.debug("nPorts: " + str(nPorts))
        self.logger.debug("nHx: " + str(nHx))

        tool = Type1924_TesPlugFlow()

        inputs = {
            "nUnit": 50,
            "nType": self.storageType,
            "nTes": self.nTes,
            "nPorts": nPorts,
            "nHx": nHx,
            "nHeatSources": 1,
        }

        directPairsPorts = []
        for directPortPair in self.directPortPairs:
            Tname = "T" + directPortPair.fromPort.connectionList[0].displayName
            side = directPortPair.side
            Mfrname = "Mfr" + directPortPair.fromPort.connectionList[0].displayName
            Trev = "T" + directPortPair.toPort.connectionList[0].displayName

            inputPos = directPortPair.relativeInputHeight
            outputPos = directPortPair.relativeOutputHeight

            directPairsPort = {
                "T": Tname,
                "side": side,
                "Mfr": Mfrname,
                "Trev": Trev,
                "zIn": inputPos,
                "zOut": outputPos,
            }
            directPairsPorts.append(directPairsPort)

        heatExchangerPorts = []
        for heatExchanger in self.heatExchangers:
            HxName = heatExchanger.displayName
            incomingConnection = heatExchanger.port1.connectionList[0]
            Tname = "T" + incomingConnection.displayName
            Mfrname = "Mfr" + incomingConnection.displayName

            outgoingConnection = heatExchanger.port2.connectionList[0]
            Trev = "T" + outgoingConnection.displayName

            inputPos = heatExchanger.relativeInputHeight
            outputPos = heatExchanger.relativeOutputHeight

            heatExchangerPort = {
                "Name": HxName,
                "T": Tname,
                "Mfr": Mfrname,
                "Trev": Trev,
                "zIn": inputPos,
                "zOut": outputPos,
                "cp": "cpwat",
                "rho": "rhowat",
            }

            heatExchangerPorts.append(heatExchangerPort)

        auxiliaryPorts = []
        for i in range(inputs["nHeatSources"]):
            dictInputAux = {"zAux": 0.0, "qAux": 0.0}
            auxiliaryPorts.append(dictInputAux)

        exportPath = os.path.join(self.path, self.displayName + ".ddck")
        self.logger.debug(exportPath)

        tool.setInputs(inputs, directPairsPorts, heatExchangerPorts, auxiliaryPorts)

        tool.createDDck(self.path, self.displayName, self.displayName, typeFile="ddck")
        self.loadedTo = self.path

    def debugConn(self):
        self.logger.debug("Debugging conn")
        errorConnList = ""
        for directPort in self.directPortPairs:
            stFromPort = directPort.fromPort
            stToPort = directPort.toPort
            toPort1 = stFromPort.connectionList[0].toPort
            fromPort2 = stToPort.connectionList[0].fromPort
            connName1 = stFromPort.connectionList[0].displayName
            connName2 = stToPort.connectionList[0].displayName

            if stFromPort != toPort1:
                errorConnList = errorConnList + connName1 + "\n"
            if stToPort != fromPort2:
                errorConnList = errorConnList + connName2 + "\n"
        if errorConnList != "":
            msgBox = QMessageBox()
            msgBox.setText(
                "%s is connected wrongly, right click StorageTank to invert connection."
                % (errorConnList)
            )
            msgBox.exec()
            noError = False
        else:
            noError = True

        return noError

    def checkConnExists(self):
        for hx in self.heatExchangers:
            if not hx.port1.connectionList:
                return False
            if not hx.port2.connectionList:
                return False

        for ports in self.leftDirectPortPairsPortItems:
            if not ports.connectionList:
                return False

        for ports in self.rightDirectPortPairsPortItems:
            if not ports.connectionList:
                return False

        return True

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
        # for i in range(1, self.model.columnCount()-1):
        #     self.tree.hideColumn(i)
        self.tree.setMinimumHeight(200)
        self.tree.setSortingEnabled(True)
        self.parent.parent().splitter.addWidget(self.tree)

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
        shutil.rmtree(self.path)
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
        destPath = os.path.join(os.path.split(self.path)[0], self.displayName)
        if os.path.split(self.path)[-1] == "" or os.path.split(self.path)[-1] == "ddck":
            os.makedirs(destPath)
        else:
            if os.path.exists(self.path):
                os.rename(self.path, destPath)
        self.path = destPath
        self.logger.debug(self.path)
