import os
import random
import sys
from pathlib import Path

from PyQt5.QtCore import QPointF
from PyQt5.QtGui import QIcon, QColor
from PyQt5.QtWidgets import QMenu, QMessageBox, QFileDialog

from trnsysGUI.BlockItem import BlockItem
from trnsysGUI.ConfigStorage import ConfigStorage
from trnsysGUI.Connector import Connector
from trnsysGUI.HeatExchanger import HeatExchanger
from trnsysGUI.PortItem import PortItem
from trnsysGUI.TeePiece import TeePiece
from trnsysGUI.Connection import Connection
from trnsysGUI.Types.createType1924 import Type1924_TesPlugFlow


class StorageTank(BlockItem):
    delta = 4

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

        self.nTes = self.parent.parent().idGen.getStoragenTes()
        self.storageType = self.parent.parent().idGen.getStorageType()

        self.changeSize()

    # Setter functions
    def setParent(self, p):
        print("Setting parent of Storage Tank (and its hx)")
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
                self.inputs[-1].setPos(-2 * StorageTank.delta,
                                       hAbs)  # Not sure if this is the correct access to class variables
            else:
                self.outputs.append(PortItem('i', 0, self))
                self.outputs[-1].setPos(-2 * StorageTank.delta,
                                        hAbs)
        else:
            if s == 'o':
                self.inputs.append(PortItem('o', 0, self))
                self.inputs[-1].setPos(self.w + 2 * StorageTank.delta, hAbs)
            else:
                self.outputs.append(PortItem('o', 0, self))
                self.outputs[-1].setPos(self.w + 2 * StorageTank.delta, hAbs)


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
                print("Found an existing input port")
                # port1 = i

            if i.pos().y() == hAbsO:
                print("Can't create a new output over an existing input")
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
            port1.setPos(-2 * StorageTank.delta, hAbsI)
            port2.setPos(-2 * StorageTank.delta, hAbsO)
            port1.side = 0
            port2.side = 0
        else:
            port1.setPos(self.w + 2 * StorageTank.delta, hAbsI)
            port2.setPos(self.w + 2 * StorageTank.delta, hAbsO)
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
            self.directPortConnsForList.append(c)
            return c

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

        print(" " * 3 * d + "In port1 " + str(port1) + "at depth " + str(d))
        print(" " * 3 * d + "Connection list is " + str(port1.connectionList))
        print(" " * 3 * d + "Parent is " + str(port1.parent))

        if port1 is port2:
            print(" " * 3 * d + "Found a connection between port 1 and port 2")

        if d == maxhops:
            print(" " * 3 * d + "Port + " + str(port1) + " is returning.")
            return

        if port1.parent.name == 'TeePiece.png':
            # print("We are at T piece " + str(port1.parent))
            conns = port1.parent.getConnections()
            # print("Connections of T piece are " + str(conns))
            for c in conns:
                print(" " * 3 * d + "Conns")
                if c.fromPort.parent is port1.parent:
                    if (not c.fromPort.visited) and (not c.toPort.visited):
                        c.fromPort.visited = True
                        self.checkConnectInside(c.toPort, port2, maxhops, d + 1)

                if c.toPort.parent is port1.parent:
                    if (not c.toPort.visited) and (not c.fromPort.visited):
                        c.toPort.visited = True
                        self.checkConnectInside(c.fromPort, port2, maxhops, d + 1)

        if port1.parent.name == 'StorageTank':
            # print("We are at " + str(port1.parent))

            if d > 1:
                print(" " * 3 * d + "port1 " + str(port1) + " at StorageTank is returning.")
                return

            for j in port1.connectionList:
                if j.toPort is port1:
                    print(" " * 3 * d + "toPort is port1 is " + str(port1))
                    print(" " * 3 * d + "fromPort is " + str(j.fromPort) + "\n")
                    if not j.fromPort.visited:
                        self.checkConnectInside(j.fromPort, port2, maxhops, d + 1)
                    else:
                        print(" " * 3 * d + "Port was already visited, at depth " + str(d) + " at Storage Tank")
                if j.fromPort is port1:
                    print(" " * 3 * d + "fromPort is port1" + str(port1))
                    print(" " * 3 * d + "toPort is " + str(j.toPort) + "\n")
                    if not j.toPort.visited:
                        self.checkConnectInside(j.toPort, port2, maxhops, d + 1)
                    else:
                        print(" " * 3 * d + "Port was already visited, at depth " + str(d) + " at Storage Tank")

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
            print("side element" + si.parent.displayName)
        tempArrConn = []

        # Copy of the corresponding ports
        side_test = side

        # Assert that the storage has at least 2 ports at side
        if len(side) < 2:
            print("Error: storage needs at least 2 ports on a side")
            return

        if len(side) == 2:
            print("Only 2 ports in side list")
            print("ports have " + str(side[0].parent) + str(side[1].parent))

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
        # print("Self.parent.parent()" + str(self.parent.parent()))
        layer = 1
        while len(side) > 2:
            mem = []
            if len(side) % 2 == 0:
                x = len(side)
                print("Even number of ports in side")
            else:
                x = len(side) - 1
                mem.append(side[x])
                # print("Uneven " + side(x))

            for i in range(0, x, 2):
                tpiece = TeePiece("TeePiece", self.parent)
                tpiece.displayName = "TeeTes" + self.displayName + sideVar + str(tpiece.id)
                tpiece.setVisible(False)
                self.parent.scene().addItem(tpiece)
                tpList.append(tpiece)

                c1 = Connection(side[i], tpiece.inputs[0], True, self.parent.parent())
                c2 = Connection(tpiece.inputs[1], side[i + 1], True, self.parent.parent())
                print("c1 is from " + side[i].parent.displayName + " to " + tpiece.inputs[0].parent.displayName)
                print("c2 is from " + tpiece.inputs[1].parent.displayName + " to " + side[i+1].parent.displayName)
                if layer>1:
                    c1.firstS.setVisible(False)
                    c2.firstS.setVisible(False)
                    c1.hiddenGenerated = True
                    c2.hiddenGenerated = True

                resId = ""
                for j in c1.displayName:
                    if j.isdigit():
                        resId += str(j)

                # print("c1 name before is " + c1.displayName)
                c1.displayName = "PiTes" + sideVar + self.displayName + "_" + resId
                # print("c1 name is " + c1.displayName)

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
            # print(str(len(side)))

        lastC = Connection(side[0], side[1], True, self.parent.parent())
        lastC.firstS.setVisible(False)
        print("lastc is from " + side[0].parent.displayName + " to " + side[1].parent.displayName)
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
                    print("This is a real connection " + str(t.displayName))
                    if len(s.connectionList) > 0:
                        t.displayName = s.connectionList[0].displayName # + "GEN"
                        t.setClone(True)
                    else:
                        print("Found a port outside that has no connection to inside")

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

        print("ports have " + str(side[0].parent) + str(side[1].parent))

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
            print("Encoding a storage tank")

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
                print("This port is part of a manual port pair ")
                for innerC in manP.connectionList:
                    print("There is a connection")
                    if innerC.fromPort is manP and type(innerC.toPort.parent) is StorageTank \
                            and not innerC.toPort.portPairVisited:
                        print("Found the corresponding port")

                        portPairDct = {"Port1ID": manP.id}

                        b = self.hasManPortById(manP.id)

                        print("side encoded is" + str(b))

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

                        print("Found the corresponding port")

                        portPairDct = {"Port2ID": manP.id}

                        b = self.hasManPortById(manP.id)

                        print("side encoded is" + str(b))

                        portPairDct["Side"] = b
                        portPairDct["Port2offset"] = float(manP.scenePos().y() - self.scenePos().y())
                        portPairDct["Port1ID"] = innerC.fromPort.id
                        portPairDct["Port1offset"] = float(innerC.fromPort.scenePos().y() - self.scenePos().y())
                        portPairDct["ConnDisName"] = innerC.displayName
                        portPairDct["ConnID"] = innerC.id
                        portPairDct["ConnCID"] = innerC.connId
                        portPairDct["trnsysID"] = innerC.trnsysId

                        # print("Portpairlist is " + str(portPairDct))
                        portPairList.append(portPairDct)

                        # innerC.deleteConn()

                    else:
                        print("Did not found the corresponding (inner) port")

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
        print("Loading a Storage in Decoder")
        
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
            print("Printing port pair")
            print(x)

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
            # print(kwargs)
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
            print("Printing port pair")
            print(x)

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
        print("storage input list " + str(self.inputs))
        print("storage outputs list " + str(self.outputs))
        print("storage leftside " + str(self.leftSide))
        print("storage rightside " + str(self.rightSide))
        self.parent.parent().dumpInformation()

    def deleteBlockDebug(self):
        print("Listing all connections")
        conns = []
        for p in self.inputs + self.outputs:
            for c in p.connectionList:
                conns.append(c)

        [print(
            c.displayName + ", fromPort: " + c.fromPort.parent.displayName + ", toPort: " + c.toPort.parent.displayName)
         for c in conns]

    def printPortNb(self):
        print("ST has "+ str(self.inputs) + " and " + str(self.outputs))

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
        print("Block " + str(self) + " is deleting itself (" + self.displayName + ")")
        self.deleteConns()
        print("self.parent.parent" + str(self.parent.parent()))
        self.parent.parent().trnsysObj.remove(self)
        print("deleting block " + str(self) + self.displayName)
        print("self.scene is" + str(self.parent.scene()))
        self.parent.scene().removeItem(self)
        del self


    # Export related
    def exportBlackBox(self):
        equationNr = 0
        resStr = ""

        for p in self.inputs + self.outputs:
            if not p.isFromHx:
                if p.side == 0:
                    lr = "Left"
                else:
                    lr = "Right"
                resStr += "T" + self.displayName + "Port" + lr + str(
                    int(100 * (1 - (p.scenePos().y() - p.parent.scenePos().y()) / p.parent.h))) + "=1\n"
                equationNr += 1
                continue
            else:
                # Check if there is at least one internal connection
                # p.name == i to only allow one temperature entry per hx
                # Prints the name of the Hx Connector element.
                # Assumes that the Other port has no connection except to the storage
                if len(p.connectionList) > 0 and p.name == 'i':
                    # f += "T" + p.connectionList[1].displayName + "=1\n"
                    print("dds " + p.connectionList[1].displayName)
                    print("dds " + p.connectionList[1].fromPort.connectionList[1].toPort.parent.displayName)
                    print("dds " + p.connectionList[1].fromPort.connectionList[1].fromPort.parent.displayName)
                    # print("dds " + p.connectionList[2].displayName)

                    # p is a hx port; the external port has two connections, so the second one yields the hx connector

                    # Here the Hx name is printed.
                    if p.connectionList[1].fromPort is p:
                        # resStr += "T" + p.connectionList[1].toPort.connectionList[1].toPort.parent.displayName + "=1\n"
                        resStr += "T" + p.connectionList[0].displayName + "=1\n"
                    else:
                        # resStr += "T" + p.connectionList[1].fromPort.connectionList[1].toPort.parent.displayName + "=1\n"
                        resStr += "T" + p.connectionList[0].displayName + "=1\n"

                    equationNr += 1

        return resStr, equationNr

    def exportParametersFlowSolver(self, descConnLength):
        return "", 0

    def exportInputsFlowSolver1(self):
        return "", 0

    def exportInputsFlowSolver2(self):
        return self.exportInputsFlowSolver1()

    def exportOutputsFlowSolver(self, prefix, abc, equationNumber, simulationUnit):
        return "", equationNumber, 0

    def exportDck(self):

        noError = self.debugConn()

        if not noError:
            qmb = QMessageBox()
            qmb.setText("Ignore connection errors and continue with export?")
            qmb.setStandardButtons(QMessageBox.Save | QMessageBox.Cancel)
            qmb.setDefaultButton(QMessageBox.Cancel)
            ret = qmb.exec()
            if ret == QMessageBox.Save:
                print("Overwriting")
                # continue
            else:
                print("Canceling")
                return

        nPorts = len(self.directPortConnsForList)
        nHx = len(self.heatExchangers)

        if getattr(sys, 'frozen', False):
            ROOT_DIR = os.path.dirname(sys.executable)
        elif __file__:
            ROOT_DIR = os.path.dirname(__file__)
        # filePath = os.path.join(ROOT_DIR, 'ddck')
        filepaths = os.path.join(ROOT_DIR, 'filepaths')
        with open(filepaths, 'r') as file:
            data = file.readlines()
        filePath = (data[2][:-1])
        fileName = self.parent.parent().parent().currentFile
        print(fileName)

        if '\\' in fileName:
            name = fileName.split('\\')[-1][:-5]
        elif '/' in fileName:
            name = fileName.split('/')[-1][:-5]
        else:
            name = fileName
        name = name + '_nTes' + str(self.nTes)

        print("Storage Type:", self.storageType)
        print("nTes:", self.nTes)
        print("nPorts:", nPorts)
        print("nHx:", nHx)

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
            Mfrname = "Mfr" + self.directPortConnsForList[i].fromPort.connectionList[1].displayName
            Trev = "T" + self.directPortConnsForList[i].toPort.connectionList[1].displayName
            inputPos = (100-100*self.directPortConnsForList[i].fromPort.pos().y()/self.h)/100
            outputPos = (100 - 100 * self.directPortConnsForList[i].toPort.pos().y() / self.h)/100
            connectorsPort[i] = {"T": Tname, "Mfr": Mfrname, "Trev": Trev, "zIn": inputPos, "zOut": outputPos}

        for i in range(inputs["nHx"]):
            Tname = "T" + self.heatExchangers[i].port1.connectionList[1].displayName
            Mfrname = "Mfr" + self.heatExchangers[i].port1.connectionList[1].displayName
            Trev = "T" + self.heatExchangers[i].port2.connectionList[1].displayName
            inputPos = self.heatExchangers[i].input / 100
            outputPos = self.heatExchangers[i].output / 100
            connectorsHx[i] = {"T": Tname, "Mfr": Mfrname, "Trev": Trev, "zIn": inputPos, "zOut": outputPos, "cp": "cpwat", "rho": "rhowat"}

        exportPath = os.path.join(filePath, name+'.ddck')
        print(exportPath)
        if Path(exportPath).exists():
            qmb = QMessageBox()
            qmb.setText("Warning: " +
                        "An export file exists already. Do you want to overwrite or cancel?")
            qmb.setStandardButtons(QMessageBox.Save | QMessageBox.Cancel)
            qmb.setDefaultButton(QMessageBox.Cancel)
            ret = qmb.exec()
            if ret == QMessageBox.Save:
                print("Overwriting")
                # continue
            else:
                print("Canceling")
                return
        else:
            # Export file does not exist yet
            pass

        tool.setInputs(inputs, connectorsPort, connectorsHx, connectorsAux)

        tool.createDDck(filePath, name, self.displayName, typeFile="ddck")

    def loadDck(self):
        print("Opening diagram")
        # self.centralWidget.delBlocks()
        fileName = QFileDialog.getOpenFileName(self.dia, "Open diagram", filter="*.ddck")[0]
        if fileName != '':
            self.dckFilePath = fileName
        else:
            print("No filename chosen")

    def debugConn(self):
        print("Debugging conn")
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
