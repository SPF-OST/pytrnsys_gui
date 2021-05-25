# pylint: skip-file
# type: ignore

import os
import random
import shutil
import typing as _tp

from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QMenu, QMessageBox, QTreeView

import trnsysGUI.images as _img
import trnsysGUI.storage_tank.model as _model
from trnsysGUI.BlockItem import BlockItem
from trnsysGUI.ConfigStorage import ConfigStorage
from trnsysGUI.Connection import Connection
from trnsysGUI.Connector import Connector
from trnsysGUI.DirectPortPair import DirectPortPair
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

        self.heatExchangers = []

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
            for p in [dpp.connection.fromPort, dpp.connection.toPort]
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

    def createAndAddDirectPortPair(
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
        self.inputs.append(directPortPair.connection.fromPort)
        self.outputs.append(directPortPair.connection.toPort)

        return directPortPair

    def _createDirectPortPair(
        self,
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
                Connection(port1, port2, True, self.parent.parent()),
                relativeInputHeight,
                relativeOutputHeight,
                isOnLeftSide,
            )
            return directPortPair

        port1.id = kwargs["fromPortId"]
        port2.id = kwargs["toPortId"]

        connection = Connection(
            port1,
            port2,
            True,
            self.parent.parent(),
            fromPortId=kwargs["fromPortId"],
            toPortId=kwargs["toPortId"],
            segmentsLoad=[],
            cornersLoad=[],
            loadedConn=True,
        )

        connection.displayName = kwargs["connDispName"]
        connection.id = kwargs["connId"]
        connection.connId = kwargs["connCid"]
        connection.trnsysId = kwargs["trnsysConnId"]

        if port1.side == 0:
            connection.side = "Left"
        elif port1.side == 2:
            connection.side = "Right"

        directPortPair = DirectPortPair(
            connection, relativeInputHeight, relativeOutputHeight, isOnLeftSide
        )

        return directPortPair

    def modifyPortPosition(self, connectionName, newHeights):
        matchingDirectPortPairs = [
            dpp
            for dpp in self.directPortPairs
            if dpp.connection.displayName == connectionName
        ]
        if len(matchingDirectPortPairs) != 1:
            raise RuntimeError(
                f"Found no or multiple direct ports with name {connectionName}."
            )
        directPortPair = matchingDirectPortPairs[0]

        x = 0 if directPortPair.isOnLeftSide else self.w

        relativeInputHeight = (
            newHeights[0] / 100
            if newHeights[0] != ""
            else directPortPair.relativeInputHeight
        )
        directPortPair.relativeInputHeight = relativeInputHeight
        absoluteInputHeight = relativeInputHeight * self.h
        directPortPair.connection.fromPort.setPos(x, absoluteInputHeight)

        relativeOutputHeight = (
            newHeights[1] / 100
            if newHeights[1] != ""
            else directPortPair.relativeOutputHeight
        )
        directPortPair.relativeOutputHeight = relativeOutputHeight
        absoluteOutputHeight = relativeOutputHeight * self.h
        directPortPair.connection.toPort.setPos(x, absoluteOutputHeight)

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

    def connectInside(self, side, side2, tpList, sideVar):
        """
        Function generating the internal connections of the StorageTank direct ports
        Parameters
        ----------
        side : :obj:`List` of :obj:`PortItem`
        External Ports to which the generated elements are connected to

        side2 : :obj:`List` of :obj:`PortItems`
        StorageTank direct ports

        tpList :obj:`List` of :obj:`TeePiece` or :obj:`Connector`
        List of elements that should be deleted after the Trnsys export

        sideVar : str
        String added to the name of the generated elements

        Returns
        -------

        """
        # Side should be list of all ports to the same side
        # Side is used in this function to store the nodes of one layer
        for si in side:
            self.logger.debug("side element" + si.parent.displayName)
        tempArrConn = []

        # Copy of the corresponding ports
        side_test = side

        # Assert that the storage has at least 2 ports at side
        if len(side) < 2:
            self.logger.debug("Error: storage needs at least 2 ports on a side")
            return

        if len(side) == 2:
            self.logger.debug("Only 2 ports in side list")
            self.logger.debug("ports have " + str(side[0].parent) + str(side[1].parent))

            connector = Connector("Connector", self.parent, storagePorts=side2)
            connector.displayName = (
                "Conn" + self.displayName + sideVar + str(connector.id)
            )

            # Used for recognizing it to print the temperature of the storage ports
            connector.inFirstRow = True
            connector.setVisible(False)

            self.parent.scene().addItem(connector)
            tpList.append(connector)

            # This makes the virtual connections in the same direction as the ones they replace
            # Check if external connections to the storagetank have storage ports as fromPorts or toPorts
            # if side[0] has toPort at storage: connector on second place
            if side[0].connectionList[0].fromPort is side[0]:
                c1 = Connection(
                    side[0], connector.inputs[0], True, self.parent.parent()
                )
            else:
                c1 = Connection(
                    connector.inputs[0], side[0], True, self.parent.parent()
                )
                pass

            if side[1].connectionList[0].fromPort is side[1]:
                c2 = Connection(
                    side[1], connector.inputs[0], True, self.parent.parent()
                )
            else:
                c2 = Connection(
                    connector.inputs[0], side[1], True, self.parent.parent()
                )
                pass

            # Check where the fact is used that connector is at fromPort!

            c1.displayName = side[0].connectionList[0].displayName
            c1.isStorageIO = True
            c2.displayName = side[1].connectionList[0].displayName
            c2.isStorageIO = True
            return

        h = 20
        # self.logger.debug("Self.parent.parent()" + str(self.parent.parent()))
        layer = 1
        while len(side) > 2:
            mem = []
            if len(side) % 2 == 0:
                x = len(side)
                self.logger.debug("Even number of ports in side")
            else:
                x = len(side) - 1
                mem.append(side[x])
                # self.logger.debug("Uneven " + side(x))

            for i in range(0, x, 2):
                tpiece = TeePiece("TeePiece", self.parent)
                tpiece.displayName = (
                    "TeeTes" + self.displayName + sideVar + str(tpiece.id)
                )
                tpiece.setVisible(False)
                self.parent.scene().addItem(tpiece)
                tpList.append(tpiece)

                c1 = Connection(side[i], tpiece.inputs[0], True, self.parent.parent())
                c2 = Connection(
                    tpiece.inputs[1], side[i + 1], True, self.parent.parent()
                )
                self.logger.debug(
                    "c1 is from "
                    + side[i].parent.displayName
                    + " to "
                    + tpiece.inputs[0].parent.displayName
                )
                self.logger.debug(
                    "c2 is from "
                    + tpiece.inputs[1].parent.displayName
                    + " to "
                    + side[i + 1].parent.displayName
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
                c1.displayName = "PiTes" + sideVar + self.displayName + "_" + resId
                # self.logger.debug("c1 name is " + c1.displayName)

                resId = ""

                for j in c2.displayName:
                    if j.isdigit():
                        resId += str(j)

                c2.displayName = "PiTes" + sideVar + self.displayName + "_" + resId

                tempArrConn.append(c1)
                tempArrConn.append(c2)

                # self.parent.addItem(QGraphicsEllipseItem(h, i * 10, 3, 3))

                if i == 0:
                    mem.insert(0, tpiece.outputs[0])
                else:
                    mem.insert(-1, tpiece.outputs[0])

            side = mem
            layer += 1
            h += 20
            # self.logger.debug(str(len(side)))

        lastC = Connection(side[0], side[1], True, self.parent.parent())
        lastC.firstS.setVisible(False)
        self.logger.debug(
            "lastc is from "
            + side[0].parent.displayName
            + " to "
            + side[1].parent.displayName
        )
        resId = ""
        for j in lastC.displayName:
            if j.isdigit():
                resId += str(j)
        lastC.displayName = "PiTes" + sideVar + self.displayName + "_" + resId

        if len(side2) > 2:
            lastC.hiddenGenerated = True

        # Here the virtual pipes clone the name of their corresponding real pipe
        # Could be used to set a new attribute generatedPrinted
        for s in side_test:
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

        # If tpieces were generated, the first len(side_test) ones have to be marked as firstRow
        for x in tpList[: len(side_test)]:
            x.inFirstRow = True

        # self.checkConnectInside(self.inputs[0], self.inputs[3], 6, 1)

    def connectHxs(self, side, side2, connList, lr, heatX):
        """
        Adds a Connector block and connections to the external blocks (both virtual)

        Parameters
        ----------
        side : :obj:`List` of :obj:`PortItem`
        List of corresponding (external, to connect) PortItems

        side2 : :obj:`List` of :obj:`PortItem`
        Pair of Hx ports

        connList
        lr : str
        String that gets added to the generated element's name
        heatX
        HeatExchanger the ports are part of

        Returns
        -------

        """

        self.logger.debug("ports have " + str(side[0].parent) + str(side[1].parent))

        connector = Connector("Connector", self.parent, storagePorts=side2)
        connector.displayName = heatX.displayName
        # connector.displayName = "Hx" + self.displayName + lr + str(int(100 - min([p.y() for p in side2])))

        if side[0].connectionList[0].fromPort is side[0]:
            c1 = Connection(side[0], connector.inputs[0], True, self.parent.parent())
        else:
            c1 = Connection(connector.inputs[0], side[0], True, self.parent.parent())
            pass

        if side[1].connectionList[0].fromPort is side[1]:
            c2 = Connection(side[1], connector.inputs[0], True, self.parent.parent())
        else:
            c2 = Connection(connector.inputs[0], side[1], True, self.parent.parent())
            pass

        connList.append(connector)
        c1.displayName = side[0].connectionList[0].displayName
        c1.isStorageIO = True
        c2.displayName = side[1].connectionList[0].displayName
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
        portPairModels = self._getDirectPortPairModelsForSerialization()
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

    def _getDirectPortPairModelsForSerialization(self):
        portPairModels = []
        for directPort in self.directPortPairs:
            connection = directPort.connection

            side = _model.Side.createFromSideNr(connection.fromPort.side)

            inputPortModel = _model.Port(
                connection.fromPort.id, directPort.relativeInputHeight
            )

            outputPortModel = _model.Port(
                connection.toPort.id, directPort.relativeOutputHeight
            )

            portPairModel = _model.PortPair(
                side, connection.displayName, inputPortModel, outputPortModel
            )

            directPortPairModel = _model.DirectPortPair(
                portPairModel, connection.id, connection.connId, connection.trnsysId
            )

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
                heatExchanger.conn.trnsysId,
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

    def decode(self, i, resConnList, resBlockList):
        offset_x = 0
        offset_y = 0
        self._decodeInternal(
            i, offset_x, offset_y, resBlockList, resConnList, shallSetNamesAndIDs=True
        )

    def _decodeInternal(
        self,
        i,
        offset_x,
        offset_y,
        resBlockList,
        resConnList,
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
            self._decodeDirectPortPair(portPairModel, resConnList, shallSetNamesAndIDs)

        resBlockList.append(self)

    def _decodeDirectPortPair(
        self,
        portPairModel: _model.DirectPortPair,
        resConnList,
        shallSetNamesAndIDs: bool,
    ):
        portPair = portPairModel.portPair

        name = portPair.name if shallSetNamesAndIDs else portPair.name + "New"

        directPortPair = self.createAndAddDirectPortPair(
            isOnLeftSide=portPair.side == _model.Side.LEFT,
            relativeInputHeight=portPair.inputPort.relativeHeight,
            relativeOutputHeight=portPair.outputPort.relativeHeight,
            storageTankHeight=self.h,
            fromPortId=portPair.inputPort.id,
            toPortId=portPair.outputPort.id,
            connId=portPairModel.id,
            connCid=portPairModel.connectionId,
            connDispName=name,
            trnsysConnId=portPairModel.trnsysId,
            loadedConn=True,
        )

        resConnList.append(directPortPair.connection)

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
            connTrnsysID=heatExchangerModel.connectionTrnsysId,
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
        self.dia = ConfigStorage(self, self.scene().parent())

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
        dictInput = {
            "T": "Null",
            "Mfr": "Null",
            "Trev": "Null",
            "zIn": 0.0,
            "zOut": 0.0,
        }
        dictInputHx = {
            "T": "Null",
            "Mfr": "Null",
            "Trev": "Null",
            "zIn": 0.0,
            "zOut": 0.0,
            "cp": 0.0,
            "rho": 0.0,
        }
        dictInputAux = {"zAux": 0.0, "qAux": 0.0}

        connectorsPort = []
        connectorsHx = []
        connectorsAux = []

        # *dck TRNSYS file that you can execute
        # *ddck text file wchich reporesents a peice of dck

        for i in range(inputs["nPorts"]):
            connectorsPort.append(dictInput)

        for i in range(inputs["nHx"]):
            connectorsHx.append(dictInputHx)

        for i in range(inputs["nHeatSources"]):
            connectorsAux.append(dictInputAux)

        for i in range(inputs["nPorts"]):
            connection = self.directPortPairs[i].connection
            Tname = "T" + connection.fromPort.connectionList[1].displayName
            side = connection.side
            Mfrname = "Mfr" + connection.fromPort.connectionList[1].displayName
            Trev = "T" + connection.toPort.connectionList[1].displayName
            inputPos = (100 - 100 * connection.fromPort.pos().y() / self.h) / 100
            outputPos = (100 - 100 * connection.toPort.pos().y() / self.h) / 100
            connectorsPort[i] = {
                "T": Tname,
                "side": side,
                "Mfr": Mfrname,
                "Trev": Trev,
                "zIn": inputPos,
                "zOut": outputPos,
            }

        for i in range(inputs["nHx"]):
            HxName = self.heatExchangers[i].displayName
            Tname = "T" + self.heatExchangers[i].port1.connectionList[1].displayName
            Mfrname = "Mfr" + self.heatExchangers[i].port1.connectionList[1].displayName
            Trev = "T" + self.heatExchangers[i].port2.connectionList[1].displayName
            inputPos = self.heatExchangers[i].relativeInputHeight / 100
            outputPos = self.heatExchangers[i].relativeOutputHeight / 100
            connectorsHx[i] = {
                "Name": HxName,
                "T": Tname,
                "Mfr": Mfrname,
                "Trev": Trev,
                "zIn": inputPos,
                "zOut": outputPos,
                "cp": "cpwat",
                "rho": "rhowat",
            }

        exportPath = os.path.join(self.path, self.displayName + ".ddck")
        self.logger.debug(exportPath)

        tool.setInputs(inputs, connectorsPort, connectorsHx, connectorsAux)

        tool.createDDck(self.path, self.displayName, self.displayName, typeFile="ddck")
        self.loadedTo = self.path

    def loadDck(self):
        self.logger.debug("Opening diagram")
        self.exportDck()
        filePath = self.model.rootPath()
        shutil.copy(self.loadedTo, filePath)

    def debugConn(self):
        self.logger.debug("Debugging conn")
        errorConnList = ""
        for i in range(len(self.directPortPairs)):
            connection = self.directPortPairs[i].connection

            stFromPort = connection.fromPort
            stToPort = connection.toPort
            toPort1 = connection.fromPort.connectionList[1].toPort
            fromPort2 = connection.toPort.connectionList[1].fromPort
            connName1 = connection.fromPort.connectionList[1].displayName
            connName2 = connection.toPort.connectionList[1].displayName

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
            if len(hx.port1.connectionList) < 2:
                return False
            if len(hx.port2.connectionList) < 2:
                return False

        for ports in self.leftDirectPortPairsPortItems:
            if len(ports.connectionList) < 2:
                return False

        for ports in self.rightDirectPortPairsPortItems:
            if len(ports.connectionList) < 2:
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
