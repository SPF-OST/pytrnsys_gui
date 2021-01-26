import os
import glob
import random
import shutil
import sys
from pathlib import Path

from PyQt5.QtCore import QPointF
from PyQt5.QtGui import QIcon, QColor
from PyQt5.QtWidgets import QMenu, QMessageBox, QFileDialog, QTreeView

from trnsysGUI.BlockItem import BlockItem
from trnsysGUI.ConfigStorage import ConfigStorage
from trnsysGUI.Connector import Connector
from trnsysGUI.HeatExchanger import HeatExchanger
from trnsysGUI.MyQFileSystemModel import MyQFileSystemModel
from trnsysGUI.MyQTreeView import MyQTreeView
from trnsysGUI.PortItem import PortItem
from trnsysGUI.TeePiece import TeePiece
from trnsysGUI.Connection import Connection
from trnsysGUI.Types.createType1924 import Type1924_TesPlugFlow


class StorageTank(BlockItem):

    def __init__(self, trnsysType, parent, **kwargs):
        super(StorageTank, self).__init__(trnsysType, parent, **kwargs)

        self.parent = parent
        self.dckFilePath = ''

        self.leftSide = []
        self.rightSide = []

        self.heatExchangers = []

        self.childIds = []
        self.childIds.append(self.trnsysId)

        # List containing all the conns and blocks inside, used to input into connInside()
        self.insideConnLeft = []
        self.insideConnRight = []

        self.hxInsideConnsLeft = []
        self.hxInsideConnsRight = []

        self.directPortConnsForList = []

        self.blackBoxEquations = []

        self.nTes = self.parent.parent().idGen.getStoragenTes()
        self.storageType = self.parent.parent().idGen.getStorageType()

        self.changeSize()
        self.addTree()

    # Setter functions
    def setParent(self, p):
        self.logger.debug("Setting parent of Storage Tank (and its hx)")
        self.parent = p

        if self not in self.parent.parent().trnsysObj:
            self.parent.parent().trnsysObj.append(self)

        # TODO: Should hx be also in trnsysObj?
        for hx in self.heatExchangers:
            hx.parent = self

    def setName(self, newName):
        self.label.setPlainText(newName)
        self.displayName = newName


    # Unused
    def setSideManual(self, left, s, hAbs):
        if left:
            if s == 'i':
                self.inputs.append(PortItem('i', 0, self))
                self.inputs[-1].setPos(0.,hAbs)  # Not sure if this is the correct access to class variables
            else:
                self.outputs.append(PortItem('i', 0, self))
                self.outputs[-1].setPos(0.,hAbs)
        else:
            if s == 'o':
                self.inputs.append(PortItem('o', 0, self))
                self.inputs[-1].setPos(self.w, hAbs)
            else:
                self.outputs.append(PortItem('o', 0, self))
                self.outputs[-1].setPos(self.w,hAbs)


    # Ports related
    def setSideManualPair(self, left, hAbsI, hAbsO, **kwargs):

        port1 = None
        port2 = None
        sideNr = 0

        if left:
            tempSideList = self.leftSide
        else:
            tempSideList = self.rightSide
            sideNr = 2

        # Check first if there is already a port at entered position:
        for i in tempSideList:
            if i.pos().y() == hAbsI:
                self.logger.debug("Found an existing input port")
                # port1 = i

            if i.pos().y() == hAbsO:
                self.logger.debug("Can't create a new output over an existing input")
                # port2 = i



        if port1 is None:
            port1 = PortItem('i', sideNr, self)
            port1.setZValue(100)
            self.inputs.append(port1)
            tempSideList.append(port1)

        if port2 is None:
            port2 = PortItem('o', sideNr, self)
            port2.setZValue(100)
            self.outputs.append(port2)
            tempSideList.append(port2)

        self.childIds.append(self.parent.parent().idGen.getTrnsysID())

        if left:
            port1.setPos(0., hAbsI)
            port2.setPos(0., hAbsO)
            port1.side = 0
            port2.side = 0
        else:
            port1.setPos(self.w, hAbsI)
            port2.setPos(self.w, hAbsO)
            port1.side = 2
            port2.side = 2

        randomValue = int(random.uniform(20, 200))
        port1.innerCircle.setBrush(QColor(randomValue, randomValue, randomValue))
        port2.innerCircle.setBrush(QColor(randomValue, randomValue, randomValue))
        port1.visibleColor = QColor(randomValue, randomValue, randomValue)
        port2.visibleColor = QColor(randomValue, randomValue, randomValue)

        # Misuse of kwargs for detecting if the manual port pair is being loaded and not newly created
        if kwargs == {}:
            self.directPortConnsForList.append(Connection(port1, port2, True, self.parent.parent()))
            return
        else:
            port1.id = kwargs["fromPortId"]
            port2.id = kwargs["toPortId"]

            c = Connection(port1, port2, True, self.parent.parent(), fromPortId=kwargs["fromPortId"], toPortId=kwargs["toPortId"],
                           segmentsLoad=[], cornersLoad=[], loadedConn=True)
            c.displayName = kwargs["connDispName"]
            c.id = kwargs["connId"]
            c.connId = kwargs["connCid"]
            c.trnsysId = kwargs["trnsysConnId"]
            if port1.side == 0:
                c.side = 'Left'
            elif port1.side == 2:
                c.side = 'Right'
            self.directPortConnsForList.append(c)
            return c

    def modifyPortPosition(self,connectionName,newHeights):
        for i in range(len(self.directPortConnsForList)):
            if self.directPortConnsForList[i].displayName == connectionName:
                if self.directPortConnsForList[i].fromPort.side == 0:
                    if newHeights[0] != '':
                        absoluteHeight = (1.-newHeights[0]/100.)*self.h
                        self.directPortConnsForList[i].fromPort.setPos(0.,absoluteHeight)
                    if newHeights[1] != '':
                        absoluteHeight = (1.-newHeights[1]/100.)*self.h
                        self.directPortConnsForList[i].toPort.setPos(0.,absoluteHeight)
                elif self.directPortConnsForList[i].fromPort.side == 2:
                    if newHeights[0] != '':
                        absoluteHeight = (1.-newHeights[0]/100.)*self.h
                        self.directPortConnsForList[i].fromPort.setPos(self.w,absoluteHeight)
                    if newHeights[1] != '':
                        absoluteHeight = (1.-newHeights[1]/100.)*self.h
                        self.directPortConnsForList[i].toPort.setPos(self.w,absoluteHeight)

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
        self.logger.debug(" " * 3 * d + "Connection list is " + str(port1.connectionList))
        self.logger.debug(" " * 3 * d + "Parent is " + str(port1.parent))

        if port1 is port2:
            self.logger.debug(" " * 3 * d + "Found a connection between port 1 and port 2")

        if d == maxhops:
            self.logger.debug(" " * 3 * d + "Port + " + str(port1) + " is returning.")
            return

        if port1.parent.name == 'TeePiece.png':
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

        if port1.parent.name == 'StorageTank':
            # self.logger.debug("We are at " + str(port1.parent))

            if d > 1:
                self.logger.debug(" " * 3 * d + "port1 " + str(port1) + " at StorageTank is returning.")
                return

            for j in port1.connectionList:
                if j.toPort is port1:
                    self.logger.debug(" " * 3 * d + "toPort is port1 is " + str(port1))
                    self.logger.debug(" " * 3 * d + "fromPort is " + str(j.fromPort) + "\n")
                    if not j.fromPort.visited:
                        self.checkConnectInside(j.fromPort, port2, maxhops, d + 1)
                    else:
                        self.logger.debug(" " * 3 * d + "Port was already visited, at depth " + str(d) + " at Storage Tank")
                if j.fromPort is port1:
                    self.logger.debug(" " * 3 * d + "fromPort is port1" + str(port1))
                    self.logger.debug(" " * 3 * d + "toPort is " + str(j.toPort) + "\n")
                    if not j.toPort.visited:
                        self.checkConnectInside(j.toPort, port2, maxhops, d + 1)
                    else:
                        self.logger.debug(" " * 3 * d + "Port was already visited, at depth " + str(d) + " at Storage Tank")

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
            connector.displayName = "Conn" + self.displayName + sideVar + str(connector.id)

            # Used for recognizing it to print the temperature of the storage ports
            connector.inFirstRow = True
            connector.setVisible(False)

            self.parent.scene().addItem(connector)
            tpList.append(connector)

            # This makes the virtual connections in the same direction as the ones they replace
            # Check if external connections to the storagetank have storage ports as fromPorts or toPorts
            # if side[0] has toPort at storage: connector on second place
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
                tpiece.displayName = "TeeTes" + self.displayName + sideVar + str(tpiece.id)
                tpiece.setVisible(False)
                self.parent.scene().addItem(tpiece)
                tpList.append(tpiece)

                c1 = Connection(side[i], tpiece.inputs[0], True, self.parent.parent())
                c2 = Connection(tpiece.inputs[1], side[i + 1], True, self.parent.parent())
                self.logger.debug("c1 is from " + side[i].parent.displayName + " to " + tpiece.inputs[0].parent.displayName)
                self.logger.debug("c2 is from " + tpiece.inputs[1].parent.displayName + " to " + side[i+1].parent.displayName)
                if layer>1:
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
            layer+=1
            h += 20
            # self.logger.debug(str(len(side)))

        lastC = Connection(side[0], side[1], True, self.parent.parent())
        lastC.firstS.setVisible(False)
        self.logger.debug("lastc is from " + side[0].parent.displayName + " to " + side[1].parent.displayName)
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
                        t.displayName = s.connectionList[0].displayName # + "GEN"
                        t.setClone(True)
                    else:
                        self.logger.debug("Found a port outside that has no connection to inside")

        # If tpieces were generated, the first len(side_test) ones have to be marked as firstRow
        for x in tpList[:len(side_test)]:
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

        # c1 = Connection(side[0], connector.inputs[0], True, self.parent.parent())
        # c2 = Connection(side[1], connector.outputs[0], True, self.parent.parent())
        connList.append(connector)
        c1.displayName = side[0].connectionList[0].displayName
        c1.isStorageIO = True
        c2.displayName = side[1].connectionList[0].displayName
        c2.isStorageIO = True

    def deletePorts(self, displayName):
        pass


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
        self.pixmap = self.pixmap.scaled(self.w, self.h)
        self.setPixmap(self.pixmap)
        self.label.setPos(self.label.pos().x(), self.h)

    def updatePortPositions(self, h):
        for p in self.inputs + self.outputs:
            rel_h_old = p.pos().y() / self.h
            p.setPos(p.pos().x(), rel_h_old * (self.h + h))
            # p.setPos(rel_h_old, p.pos().x() * (self.h + h))

    def updatePortPositionsHW(self, h, w):
        for p in self.inputs + self.outputs:
            rel_h_old = p.pos().y() / self.h
            if p.side == 0:
                p.setPos(p.pos().x(), rel_h_old * (self.h + h))
            else:
                p.setPos(p.pos().x() + w, rel_h_old * (self.h + h))
            # p.setPos(rel_h_old, p.pos().x() * (self.h + h))

    def updatePortPositionsDec(self, h):
        for p in self.inputs + self.outputs:
            rel_h_old = p.pos().y() / self.h
            p.setPos(p.pos().x(), rel_h_old * (self.h - h))

    def updatePortPositionsDecHW(self, h, w):
        for p in self.inputs + self.outputs:
            rel_h_old = p.pos().y() / self.h
            if p.side == 0:
                p.setPos(p.pos().x(), rel_h_old * (self.h - h))
            else:
                p.setPos(p.pos().x() - w, rel_h_old * (self.h - h))

    def updateHxLines(self, h):
        for hx in self.heatExchangers:
            hx.updateLines(h)

    def updateHxLinesDec(self, h):
        for hx in self.heatExchangers:
            hx.updateLines(-h)


    # Encoding
    def encode(self):
        if self.isVisible():
            self.logger.debug("Encoding a storage tank")

            hxList = []
            for hx in self.heatExchangers:
                hxDct = {"DisplayName": hx.displayName}
                hxDct['ID'] = hx.id
                hxDct['ParentID'] = hx.parent.id
                hxDct['connTrnsysID'] = hx.conn.trnsysId
                # hxDct['connDispName'] = hx.conn.diplayName    # Both are set in initNew
                hxDct['Offset'] = (hx.offset.x(), hx.offset.y())
                hxDct['Width'] = hx.w
                hxDct['Height'] = hx.h
                hxDct['SideNr'] = hx.sSide
                hxDct['Port1ID'] = hx.port1.id
                hxDct['Port2ID'] = hx.port2.id

                hxList.append(hxDct)

            portPairList = []

            for manP in self.leftSide + self.rightSide:
                manP.portPairVisited = True
                self.logger.debug("This port is part of a manual port pair ")
                for innerC in manP.connectionList:
                    self.logger.debug("There is a connection")
                    if innerC.fromPort is manP and type(innerC.toPort.parent) is StorageTank \
                            and not innerC.toPort.portPairVisited:
                        self.logger.debug("Found the corresponding port")

                        portPairDct = {"Port1ID": manP.id}

                        b = self.hasManPortById(manP.id)

                        self.logger.debug("side encoded is" + str(b))

                        portPairDct["Side"] = b
                        portPairDct["Port1offset"] = float(manP.scenePos().y() - self.scenePos().y())
                        portPairDct["Port2ID"] = innerC.toPort.id
                        portPairDct["Port2offset"] = float(innerC.toPort.scenePos().y() - self.scenePos().y())
                        portPairDct["ConnDisName"] = innerC.displayName
                        portPairDct["ConnID"] = innerC.id
                        portPairDct["ConnCID"] = innerC.connId
                        portPairDct["trnsysID"] = innerC.trnsysId

                        portPairList.append(portPairDct)

                        # innerC.deleteConn()

                    elif innerC.toPort is manP and type(innerC.fromPort.parent) is StorageTank \
                            and not innerC.fromPort.portPairVisited:

                        self.logger.debug("Found the corresponding port")

                        portPairDct = {"Port2ID": manP.id}

                        b = self.hasManPortById(manP.id)

                        self.logger.debug("side encoded is" + str(b))

                        portPairDct["Side"] = b
                        portPairDct["Port2offset"] = float(manP.scenePos().y() - self.scenePos().y())
                        portPairDct["Port1ID"] = innerC.fromPort.id
                        portPairDct["Port1offset"] = float(innerC.fromPort.scenePos().y() - self.scenePos().y())
                        portPairDct["ConnDisName"] = innerC.displayName
                        portPairDct["ConnID"] = innerC.id
                        portPairDct["ConnCID"] = innerC.connId
                        portPairDct["trnsysID"] = innerC.trnsysId

                        # self.logger.debug("Portpairlist is " + str(portPairDct))
                        portPairList.append(portPairDct)

                        # innerC.deleteConn()

                    else:
                        self.logger.debug("Did not found the corresponding (inner) port")

            for manP in self.leftSide + self.rightSide:
                manP.portPairVisited = False
            dct = {}
            dct['.__BlockDict__'] = True
            dct['BlockName'] = self.name
            dct['BlockDisplayName'] = self.displayName
            dct['StoragePosition'] = (float(self.pos().x()), float(self.pos().y()))
            dct['ID'] = self.id
            dct['trnsysID'] = self.trnsysId
            dct['HxList'] = hxList
            dct['PortPairList'] = portPairList
            dct['FlippedH'] = self.flippedH
            dct['FlippedV'] = self.flippedH
            dct['GroupName'] = self.groupName
            dct['size_h'] = self.h

            # dct['RotationN'] = t.rotationN
            dictName = "Block-"

            return dictName, dct

    def decode(self, i, resConnList, resBlockList):
        self.logger.debug("Loading a Storage in Decoder")
        
        self.flippedH = i["FlippedH"]
        # self.flippedV = i["FlippedV"] # No support for vertical flip
        self.displayName = i["BlockDisplayName"]

        self.changeSize()
        self.h = i["size_h"]
        self.updateImage()

        self.setPos(float(i["StoragePosition"][0]), float(i["StoragePosition"][1]))
        self.trnsysId = i["trnsysID"]
        self.id = i["ID"]

        self.groupName = "defaultGroup"
        self.setBlockToGroup(i["GroupName"])

        # Add heat exchangers
        for h in i["HxList"]:
            hEx = HeatExchanger(h["SideNr"], h["Width"], h["Height"],
                                QPointF(h["Offset"][0], h["Offset"][1]), self, h["DisplayName"],
                                port1ID=h['Port1ID'], port2ID=h['Port2ID'],
                                connTrnsysID=h['connTrnsysID'], loadedHx=True)

            hEx.setId(h["ID"])
            hEx.port1.id = h['Port1ID']
            hEx.port2.id = h['Port2ID']

            # hxDct['ParentID'] = hx.parent.id
            # hxDct['Port2ID'] = hx.port2.id

        # Add manual inputs
        for x in i["PortPairList"]:
            self.logger.debug("Printing port pair")
            self.logger.debug(x)

            conn = self.setSideManualPair(x["Side"], x["Port1offset"], x["Port2offset"],
                                        fromPortId=x["Port1ID"], toPortId=x["Port2ID"],
                                        connId=x["ConnID"], connCid=x["ConnCID"],
                                        connDispName=x["ConnDisName"], trnsysConnId=x["trnsysID"], loadedConn=True)
            conn.id = x["ConnID"]
            conn.connId = x["ConnCID"]
            conn.trnsysId = x["trnsysID"]
            conn.displayName = x["ConnDisName"]

            resConnList.append(conn)
        resBlockList.append(self)

    def decodePaste(self, i, offset_x, offset_y, resConnList, resBlockList, **kwargs):
        self.flippedH = i["FlippedH"]
        self.changeSize()
        self.h = i["size_h"]
        self.updateImage()

        self.setPos(float(i["StoragePosition"][0]) + offset_x, float(i["StoragePosition"][1]) + offset_y)

        # Add heat exchanger
        for h in i["HxList"]:
            # self.logger.debug(kwargs)
            # sys.exit()
            # connsysConnId=kwargs["editor"].idGen.getTrnsysID()
            hEx = HeatExchanger(h["SideNr"], h["Width"], h["Height"],
                                QPointF(h["Offset"][0], h["Offset"][1]),
                                self, h["DisplayName"] + "New",
                                port1ID=h['Port1ID'], port2ID=h['Port2ID'],
                                connTrnsysID=h['connTrnsysID'], loadedHx=True)

            # hEx = HeatExchanger(h["SideNr"], h["Width"], h["Height"],
            #                     QPointF(h["Offset"][0], h["Offset"][1]),
            #                     self, h["DisplayName"] + "New",
            #                     port1ID=h['Port1ID'], port2ID=h['Port2ID'],
            #                     connTrnsysID=kwargs["editor"].idGen.getTrnsysID(), loadedHx=True)

            # hEx.setId(["ID"])
            hEx.port1.id = h['Port1ID']
            hEx.port2.id = h['Port2ID']

        # Add manual inputs
        for x in i["PortPairList"]:
            self.logger.debug("Printing port pair")
            self.logger.debug(x)

            # trnsysConnId=kwargs["editor"].idGen.getTrnsysID()
            conn = self.setSideManualPair(x["Side"], x["Port1offset"], x["Port2offset"],
                                        fromPortId=x["Port1ID"], toPortId=x["Port2ID"],
                                        connId=x["ConnID"], connCid=x["ConnCID"],
                                        connDispName=x["ConnDisName"] + "New",
                                        trnsysConnId=x["trnsysID"], loadedConn=True)

            # conn = self.setSideManualPair(x["Side"], x["Port1offset"], x["Port2offset"],
            #                               fromPortId=x["Port1ID"], toPortId=x["Port2ID"],
            #                               connId=kwargs["editor"].idGen.getID(),
            #                               connCid=kwargs["editor"].idGen.getConnID(),
            #                               connDispName=x["ConnDisName"] + "New",
            #                               trnsysConnId=kwargs["editor"].idGen.getTrnsysID(), loadedConn=True)

            resConnList.append(conn)
        resBlockList.append(self)


    # Debug
    def dumpBlockInfo(self):
        self.logger.debug("storage input list " + str(self.inputs))
        self.logger.debug("storage outputs list " + str(self.outputs))
        self.logger.debug("storage leftside " + str(self.leftSide))
        self.logger.debug("storage rightside " + str(self.rightSide))
        self.parent.parent().dumpInformation()

    def deleteBlockDebug(self):
        self.logger.debug("Listing all connections")
        conns = []
        for p in self.inputs + self.outputs:
            for c in p.connectionList:
                conns.append(c)

        [self.logger.debug(
            c.displayName + ", fromPort: " + c.fromPort.parent.displayName + ", toPort: " + c.toPort.parent.displayName)
         for c in conns]

    def printPortNb(self):
        self.logger.debug("ST has "+ str(self.inputs) + " and " + str(self.outputs))

    # Misc
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
        # c2 = menu.addAction("Set group")
        # c2.triggered.connect(self.configGroup)
        #
        # d1 = menu.addAction('Dump information')
        # d1.triggered.connect(self.dumpBlockInfo)
        #
        # e1 = menu.addAction('Inspect')
        # e1.triggered.connect(self.inspectBlock)
        #
        # e2 = menu.addAction('Print port nb')
        # e2.triggered.connect(self.printPortNb)

        e3 = menu.addAction('Export ddck')
        e3.triggered.connect(self.exportDck)

        # e4 = menu.addAction('Debug Connection')
        # e4.triggered.connect(self.debugConn)

        menu.exec_(event.screenPos())

    def mouseDoubleClickEvent(self, event):
        self.dia = ConfigStorage(self, self.scene().parent())

    def hasManPortById(self, idFind):

        res = -1

        for p in self.leftSide:
            if p.id == idFind:
                res = True

        for p in self.rightSide:
            if p.id == idFind:
                res = False
        return res

    def deleteBlock(self):
        self.logger.debug("Block " + str(self) + " is deleting itself (" + self.displayName + ")")
        self.deleteConns()
        self.logger.debug("self.parent.parent" + str(self.parent.parent()))
        self.parent.parent().trnsysObj.remove(self)
        self.logger.debug("deleting block " + str(self) + self.displayName)
        self.logger.debug("self.scene is" + str(self.parent.scene()))
        self.parent.scene().removeItem(self)
        del self


    # Export related
    def exportBlackBox(self):
        ddcxPath = os.path.join(self.path,self.displayName)
        ddcxPath = ddcxPath + ".ddcx"
        if not os.path.isfile(ddcxPath):
            self.exportDck()
        infile=open(ddcxPath,'r')
        lines=infile.readlines()
        equations = []
        for line in lines:
            if line[0] == "T":
                equations.append(line.replace("\n",""))
        return 'success', equations

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

        nPorts = len(self.directPortConnsForList)
        nHx = len(self.heatExchangers)

        # if getattr(sys, 'frozen', False):
        #     ROOT_DIR = os.path.dirname(sys.executable)
        # elif __file__:
        #     ROOT_DIR = os.path.dirname(__file__)
        # # filePath = os.path.join(ROOT_DIR, 'ddck')
        # filepaths = os.path.join(ROOT_DIR, 'filepaths.txt')
        # with open(filepaths, 'r') as file:
        #     data = file.readlines()
        # filePath = (data[2][:-1])

        # fileName = self.parent.parent().parent().currentFile
        # self.logger.debug(fileName)
        #
        # if '\\' in fileName:
        #     name = fileName.split('\\')[-1][:-5]
        # elif '/' in fileName:
        #     name = fileName.split('/')[-1][:-5]
        # else:
        #     name = fileName
        # name = name + '_nTes' + str(self.nTes)

        self.logger.debug("Storage Type:", self.storageType)
        self.logger.debug("nTes:", self.nTes)
        self.logger.debug("nPorts:", nPorts)
        self.logger.debug("nHx:", nHx)

        tool = Type1924_TesPlugFlow()

        inputs = {"nUnit": 50,
                  "nType": self.storageType,
                  "nTes": self.nTes,
                  "nPorts": nPorts,
                  "nHx": nHx,
                  "nHeatSources": 1
                  }
        dictInput = {"T": "Null", "Mfr": "Null", "Trev": "Null", "zIn": 0.0, "zOut": 0.0}
        dictInputHx = {"T": "Null", "Mfr": "Null", "Trev": "Null", "zIn": 0.0, "zOut": 0.0, "cp": 0.0, "rho": 0.0}
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
            Tname = "T" + self.directPortConnsForList[i].fromPort.connectionList[1].displayName
            side = self.directPortConnsForList[i].side
            Mfrname = "Mfr" + self.directPortConnsForList[i].fromPort.connectionList[1].displayName
            Trev = "T" + self.directPortConnsForList[i].toPort.connectionList[1].displayName
            inputPos = (100-100*self.directPortConnsForList[i].fromPort.pos().y()/self.h)/100
            outputPos = (100 - 100 * self.directPortConnsForList[i].toPort.pos().y() / self.h)/100
            connectorsPort[i] = {"T": Tname, "side": side, "Mfr": Mfrname, "Trev": Trev, "zIn": inputPos, "zOut": outputPos}

        for i in range(inputs["nHx"]):
            HxName = self.heatExchangers[i].displayName
            Tname = "T" + self.heatExchangers[i].port1.connectionList[1].displayName
            Mfrname = "Mfr" + self.heatExchangers[i].port1.connectionList[1].displayName
            Trev = "T" + self.heatExchangers[i].port2.connectionList[1].displayName
            inputPos = self.heatExchangers[i].input / 100
            outputPos = self.heatExchangers[i].output / 100
            connectorsHx[i] = {"Name": HxName, "T": Tname, "Mfr": Mfrname, "Trev": Trev, "zIn": inputPos, "zOut": outputPos, "cp": "cpwat", "rho": "rhowat"}

        # exportPath = os.path.join(filePath, name+'.ddck')
        exportPath = os.path.join(self.path,self.displayName + '.ddck')
        self.logger.debug(exportPath)
        if Path(exportPath).exists():
            qmb = QMessageBox()
            qmb.setText("Warning: " +
                        "An export file exists already. Do you want to overwrite or cancel?")
            qmb.setStandardButtons(QMessageBox.Save | QMessageBox.Cancel)
            qmb.setDefaultButton(QMessageBox.Cancel)
            ret = qmb.exec()
            if ret == QMessageBox.Save:
                self.logger.debug("Overwriting")
                # continue
            else:
                self.logger.debug("Canceling")
                return
        else:
            # Export file does not exist yet
            pass

        tool.setInputs(inputs, connectorsPort, connectorsHx, connectorsAux)

        tool.createDDck(self.path, self.displayName, self.displayName, typeFile="ddck")
        self.loadedTo = self.path

    def loadDck(self):
        self.logger.debug("Opening diagram")
        # self.centralWidget.delBlocks()
        # fileName = QFileDialog.getOpenFileName(self.dia, "Open diagram", filter="*.ddck")[0]
        # if fileName != '':
        #     self.dckFilePath = fileName
        # else:
        #     self.logger.debug("No filename chosen")
        self.exportDck()
        filePath = self.model.rootPath()
        shutil.copy(self.loadedTo, filePath)

    def debugConn(self):
        self.logger.debug("Debugging conn")
        errorConnList = ''
        for i in range(len(self.directPortConnsForList)):
            stFromPort = self.directPortConnsForList[i].fromPort
            stToPort = self.directPortConnsForList[i].toPort
            toPort1 = self.directPortConnsForList[i].fromPort.connectionList[1].toPort
            toPort2 = self.directPortConnsForList[i].toPort.connectionList[1].toPort
            fromPort1 = self.directPortConnsForList[i].fromPort.connectionList[1].fromPort
            fromPort2 = self.directPortConnsForList[i].toPort.connectionList[1].fromPort
            connName1 = self.directPortConnsForList[i].fromPort.connectionList[1].displayName
            connName2 = self.directPortConnsForList[i].toPort.connectionList[1].displayName

            # if toPort1 == stFromPort and toPort2 == stToPort:
            #     msgBox = QMessageBox()
            #     msgBox.setText("both %s and %s are input ports" % (connName1, connName2))
            #     msgBox.exec_()
            # elif fromPort1 == stFromPort and fromPort2 == stToPort:
            #     msgBox = QMessageBox()
            #     msgBox.setText("both %s and %s are output ports" % (connName1, connName2))
            #     msgBox.exec_()
            if stFromPort != toPort1:
                errorConnList = errorConnList + connName1 + '\n'
            if stToPort != fromPort2:
                errorConnList = errorConnList + connName2 + '\n'
        if errorConnList !='':
            msgBox = QMessageBox()
            msgBox.setText("%sis connected wrongly, right click StorageTank to invert connection." % (errorConnList))
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

        for ports in self.leftSide:
            if len(ports.connectionList) < 2:
                return False

        for ports in self.rightSide:
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
        # for i in range(1, self.model.columnCount()-1):
        #     self.tree.hideColumn(i)
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
        widgetToRemove = self.parent.parent().findChild(QTreeView, self.displayName+'Tree')
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
        destPath = os.path.join(os.path.split(self.path)[0],self.displayName)
        test = os.path.split(self.path)
        if os.path.split(self.path)[-1] == '' or os.path.split(self.path)[-1] == 'ddck':
            os.makedirs(destPath)
        else:
            if os.path.exists(self.path):
                os.rename(self.path, destPath)
        self.path = destPath
        self.logger.debug(self.path)
