from trnsysGUI.BlockItem import BlockItem
from trnsysGUI.ConfigStorage import ConfigStorage
from trnsysGUI.Connector import Connector
from trnsysGUI.PortItem import PortItem
from trnsysGUI.TeePiece import TeePiece
from trnsysGUI.Connection import Connection


class StorageTank(BlockItem):
    delta = 4

    def __init__(self, trnsysType, name, parent):
        super(StorageTank, self).__init__(trnsysType, name, parent)
        # self.leftConnections = 0
        # self.rightConnections = 0
        self.parent = parent

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

        return w, h

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
                port1 = i
            if i.pos().y() == hAbsO:
                print("Can't create a new output over an existing input")

        # for o in self.tempSideList:
        #     if o.pos().y() == hAbsO:
        #         print("Found an existing output port")
        #         port2 = o
        #     if o.pos().y() == hAbsI:
        #         print("Can't create a new input over an existing output")

        if port1 is None:
            port1 = PortItem('i', sideNr, self)

        if port2 is None:
            port2 = PortItem('o', sideNr, self)

        self.inputs.append(port1)
        self.outputs.append(port2)

        tempSideList.append(port1)
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

        # print("Self is " + str(self))
        # print("Self.parent is " + str(self.parent))
        # print("Self.parent.parent() is " + str(self.parent.parent()))

        # Misuse of kwargs for detecting if the manual port pair is being loaded and not newly created

        if kwargs == {}:
            Connection(port1, port2, True, self.parent.parent())
            return
        else:
            port1.id = kwargs["fromPortId"]
            port2.id = kwargs["toPortId"]
            c = Connection(port1, port2, True, self.parent.parent(), fromPortId=kwargs["fromPortId"], toPortId=kwargs["toPortId"],
                           segmentsLoad=[], cornersLoad=[])
            c.displayName = kwargs["connDispName"]
            c.id = kwargs["connId"]
            c.connId = kwargs["connCid"]
            c.trnsysId = kwargs["trnsysConnId"]

            return c

    def setLeftSideManual(self, s, hAbs):
        # Just for testing, should be properly implemented as parameters

        self.inputs.append(PortItem(s, 0, self))
        self.inputs[-1].setPos(-2 * StorageTank.delta,
                               hAbs)  # Not sure if this is the correct access to class variables

    def setRightSideManual(self, s, hAbs):
        self.inputs.append(PortItem(s, 0, self))
        self.inputs[-1].setPos(self.w + 2 * StorageTank.delta, hAbs)

    def setLeftSideAuto(self, n):
        h = self.h
        autoInputs = []

        for i in range(n):
            temp = PortItem('i', 0, self)
            self.inputs.append(temp)
            temp.setPos(-2 * StorageTank.delta, 1 / (n + 1) * h * (i + 1))
            autoInputs.append(temp)

        print("Momentarily not used")
        # self.connectInside(autoInputs, SOMELIST)

    def setRightSideAuto(self, n):
        delta = 4
        h = self.h
        autoInputs = []

        for i in range(n):
            temp = PortItem('o', 0, self)
            self.outputs.append(temp)
            temp.setPos(2 * delta + 100, 1 / (n + 1) * h * (i + 1))
            autoInputs.append(temp)

        print("Momentarily not used")
        # self.connectInside(autoInputs, SOMELIST)

    def getNotHxPorts(self):
        pass

    def checkConnectInside(self, port1, port2, maxhops, d):
        # Finds connection between the insideConnected of StorageTank but need improvement
        # Basically a depth first algorithm
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

    def checkInside2(self, port1, port2, maxdepth, d):
        # Same as checkInside, but using BFS
        pass

    def connectInside(self, side, side2, tpList, sideVar):
        # Side should be list of all ports to the same side
        # Assert that the storage has at least 2 ports at side
        # Side is used in this function to store the nodes of one layer

        # sideVar = "Right"

        # print("self.parent is " + str(self.parent))
        # print("self.parent.parent is " + str(self.parent.parent))

        tempArrConn = []
        side_test = side

        if len(side) < 2:
            print("Error: storage needs at least 2 ports on a side")
            return

        if len(side) == 2:
            print("Only 2 ports in side list")
            print("ports have " + str(side[0].parent) + str(side[1].parent))

            connector = Connector("Connector", "Connector", self.parent, storagePorts=side2)
            connector.displayName = "Conn" + self.displayName + sideVar + str(connector.id)

            # Used for recognizing it to print the temperature of the storage ports
            connector.inFirstRow = True

            connector.setVisible(False)
            self.parent.scene().addItem(connector)
            tpList.append(connector)

            c1 = Connection(side[0], connector.inputs[0], True, self.parent.parent())
            c2 = Connection(side[1], connector.outputs[0], True, self.parent.parent())
            c1.displayName = side[0].connectionList[0].displayName
            c1.isStorageIO = True
            c2.displayName = side[1].connectionList[0].displayName
            c2.isStorageIO = True
            return

        h = 20
        # print("Self.parent.parent()" + str(self.parent.parent()))
        while len(side) > 2:
            mem = []
            if len(side) % 2 == 0:
                x = len(side)
            else:
                x = len(side) - 1
                mem.append(side[x])

            for i in range(0, x, 2):
                tpiece = TeePiece("TeePiece", "TeePiece", self.parent)
                tpiece.displayName = "TPieceTes" + self.displayName + sideVar + str(tpiece.id)
                tpiece.setVisible(False)
                self.parent.scene().addItem(tpiece)
                tpList.append(tpiece)

                c1 = Connection(side[i], tpiece.inputs[0], True, self.parent.parent())
                c2 = Connection(tpiece.inputs[1], side[i + 1], True, self.parent.parent())

                resId = ""
                for j in c1.displayName:
                    if j.isdigit():
                        resId += str(j)

                # print("Res is " + resId)
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

                # c1.firstS.setVisible(False)
                # c2.firstS.setVisible(False)

                # self.parent.addItem(QGraphicsEllipseItem(h, i * 10, 3, 3))

                if i == 0:
                    mem.insert(0, tpiece.outputs[0])
                else:
                    mem.insert(-1, tpiece.outputs[0])

            side = mem
            h += 20
            # print(str(len(side)))

        lastC = Connection(side[0], side[1], True, self.parent.parent())
        lastC.firstS.setVisible(False)
        resId = ""
        for j in lastC.displayName:
            if j.isdigit():
                resId += str(j)
        lastC.displayName = "PiTes" + sideVar + self.displayName + "_" + resId

        for s in side_test:
            for t in tempArrConn:
                # print("Checking s")
                if t.fromPort is s or t.toPort is s:
                    print("This is a real connection " + str(t.displayName))
                    if len(s.connectionList) > 0:
                        t.displayName = s.connectionList[0].displayName
                    else:
                        print("Found a port outside that has no connection to inside")

        # If tpieces were generated, the first len(side_test) ones have to be marked as firstRow
        for x in tpList[:len(side_test)]:
            x.inFirstRow = True

        # self.checkConnectInside(self.inputs[0], self.inputs[3], 6, 1)

    def connectHxs(self, side, side2, connList, lr):
        # Adds a Connector block and connections to the external blocks (both virtual)
        print("ports have " + str(side[0].parent) + str(side[1].parent))

        connector = Connector("Connector", "Connector", self.parent, storagePorts=side2)
        connector.displayName = "Hx" + self.displayName + lr + str(int(100 - min([p.y() for p in side2])))
        c1 = Connection(side[0], connector.inputs[0], True, self.parent.parent())
        c2 = Connection(side[1], connector.outputs[0], True, self.parent.parent())
        connList.append(connector)
        c1.displayName = side[0].connectionList[0].displayName
        c1.isStorageIO = True
        c2.displayName = side[1].connectionList[0].displayName
        c2.isStorageIO = True

    def setParent(self, p):
        print("Setting parent of Storage Tank (and its hx)")
        self.parent = p

        if self not in self.parent.parent().trnsysObj:
            self.parent.parent().trnsysObj.append(self)

        # TODO: Should hx be also in trnsysObj
        for hx in self.heatExchangers:
            hx.parent = self

    def setName(self, newName):
        self.label.setPlainText(newName)
        self.displayName = newName

    def hasManPortById(self, idFind):

        res = -1

        for p in self.leftSide:
            if p.id == idFind:
                res = True

        for p in self.rightSide:
            if p.id == idFind:
                res = False
        return res

    def updateImage(self):
        self.pixmap = self.pixmap.scaled(100, self.h)
        self.setPixmap(self.pixmap)
        self.label.setPos(self.label.pos().x(), self.h)

    def mouseDoubleClickEvent(self, event):
        dia = ConfigStorage(self, self.scene().parent())

    def dumpBlockInfo(self):
        print("storage input list " + str(self.inputs))
        print("storage outputs list " + str(self.outputs))
        print("storage leftside " + str(self.leftSide))
        print("storage rightside " + str(self.rightSide))
        self.parent.parent().dumpInformation()

    def deleteBlock(self):
        print("Block " + str(self) + " is deleting itself (" + self.displayName + ")")
        self.deleteConns()
        print("self.parent.parent" + str(self.parent.parent()))
        self.parent.parent().trnsysObj.remove(self)
        print("deleting block " + str(self) + self.displayName)
        print("self.scene is" + str(self.parent.scene()))
        self.parent.scene().removeItem(self)
        del self

    def deleteBlockDebug(self):
        print("Listing all connections")
        conns = []
        for p in self.inputs + self.outputs:
            for c in p.connectionList:
                conns.append(c)

        [print(
            c.displayName + ", fromPort: " + c.fromPort.parent.displayName + ", toPort: " + c.toPort.parent.displayName)
         for c in conns]

    def deleteHeatExchangers(self):
        pass

    def updatePortPositions(self, h):
        for p in self.inputs + self.outputs:
            rel_h_old = p.pos().y() / self.h
            p.setPos(p.pos().x(), rel_h_old * (self.h + h))
    # def keyPressEvent(self, event):
    #     print("Pressed st")
    #
    #     super(StorageTank, self).keyPressEvent(event)