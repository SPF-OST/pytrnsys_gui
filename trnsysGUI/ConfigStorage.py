from PyQt5.QtCore import QPointF
from PyQt5.QtWidgets import QLabel, QLineEdit, QGridLayout, QHBoxLayout, QListWidget, QPushButton, QSpacerItem, \
    QVBoxLayout, QRadioButton, QDialog, QTabWidget, QWidget

from trnsysGUI.HeatExchanger import HeatExchanger


class ConfigStorage(QDialog):
    def __init__(self, storage, parent):
        super(ConfigStorage, self).__init__(parent)
        self.parent = parent
        self.storage = storage
        self.n = 0
        self.m = 0

        # Parameters:
        self.w_hx = 10
        self.h_hx = 100

        spacerHeight = 15

        self.tabs = QTabWidget()
        self.tab1 = QWidget()
        self.tab2 = QWidget()

        # Add tabs
        self.tabs.addTab(self.tab1, "Heat exchangers")
        self.tabs.addTab(self.tab2, "Direct ports")

        # VBoxLayout
        description = QLabel("Please configure the storage tank:")
        tankNameLabel = QLabel()
        tankNameLabel.setText("<b>Tank name: </b>")
        self.le = QLineEdit(self.storage.label.toPlainText())

        # connectionsLabelL = QLabel()
        # connectionsLabelL.setText("<b>Left (distributed) Ports: </b>")
        # self.leCNL = QLineEdit(str(len(self.storage.inputs)))

        # connectionsLabelR = QLabel()
        # connectionsLabelR.setText("<b>Right (distributed) Ports: </b>")
        # self.leCNR = QLineEdit(str(len(self.storage.outputs)))

        # addSideAutoButton = QPushButton("Add (distributed) ports")
        # addSideAutoButton.clicked.connect(self.addSideAuto)
        # spaceVBox = QSpacerItem(self.width(), spacerHeight)

        # Grid layout
        gl = QGridLayout()
        hxsLabel = QLabel("<b>Heat Exchangers </b>")
        gl.addWidget(hxsLabel, 0, 0, 1, 2)

        qhbL = QHBoxLayout()

        self.listWL = QListWidget()
        # self.listWL.setMinimumWidth(self.width()/2)
        # self.listWL.resize(QSize(self.listWL.minimumHeight(), self.width()/2))
        # gl.addWidget(self.listWL, 1, 0, 2, 2)
        qhbL.addWidget(self.listWL)

        self.listWR = QListWidget()
        # self.setBaseSize(QSize(100, 50))
        # gl.addWidget(self.listWR, 1, 1, 1, 2)
        qhbL.addWidget(self.listWR)

        offsetLabel = QLabel("Height offsets in percent")
        offsetLeILabel = QLabel("Input (upper port): ")
        offsetLeOLabel = QLabel("Output (lower port):")
        self.offsetLeI = QLineEdit("0")
        self.offsetLeO = QLineEdit("0")
        self.lButton = QRadioButton("Left side")
        self.rButton = QRadioButton("Right side")

        gl.addWidget(offsetLabel, 3, 0, 1, 1)
        gl.addWidget(offsetLeILabel, 4, 0, 1, 1)
        gl.addWidget(self.offsetLeI, 5, 0, 1, 3)
        gl.addWidget(offsetLeOLabel, 6, 0, 1, 1)
        gl.addWidget(self.offsetLeO, 7, 0, 1, 3)



        # hxsideHbL = QHBoxLayout()
        # hxsideHbL.addWidget(self.lButton)
        # hxsideHbL.addWidget(self.rButton)

        # gl.addLayout(hxsideHbL, 6, 0)
        self.hxNameLe = QLineEdit()
        self.hxNameLe.setPlaceholderText("Enter a name...")
        gl.addWidget(self.hxNameLe, 8, 0, 1, 3)

        gl.addWidget(self.lButton, 9, 0, 1, 1)
        gl.addWidget(self.rButton, 9, 2, 1, 1)

        addButton = QPushButton("Add...")
        addButton.clicked.connect(self.addHx)
        gl.addWidget(addButton, 10, 0, 1, 1)
        removeButton = QPushButton("Remove...")
        removeButton.clicked.connect(self.removeHxL)
        removeButton.clicked.connect(self.removeHxR)
        gl.addWidget(removeButton, 10, 1, 1, 1)
        modifyButton = QPushButton("Modify")
        modifyButton.clicked.connect(self.modifyHx)
        gl.addWidget(modifyButton, 10, 2, 1, 1)
        spaceHx = QSpacerItem(self.width(), spacerHeight)
        gl.addItem(spaceHx, 11, 0, 1, 2)

        manPortLay = QVBoxLayout()
        qhbL2 = QHBoxLayout()

        self.listWL2 = QListWidget()
        qhbL2.addWidget(self.listWL2)

        self.listWR2 = QListWidget()
        qhbL2.addWidget(self.listWR2)

        manPortLay.addLayout(qhbL2)

        manPortLabel = QLabel("<b>Set port manually</b>")
        manPortLabel2 = QLabel("Enter height in percent: ")
        portlabelUpper = QLabel("Upper port")
        self.manPortLeI = QLineEdit("0")
        portlabelLower = QLabel("Lower port")
        self.manPortLeO = QLineEdit("0")

        qhbl3 = QHBoxLayout()
        self.manlButton = QRadioButton("Left side")
        self.manrButton = QRadioButton("Right side")
        qhbl3.addWidget(self.manlButton)
        qhbl3.addWidget(self.manrButton)

        self.manAddButton = QPushButton("Add (manual) ports")
        spaceManPort = QSpacerItem(self.width(), spacerHeight)
        self.manAddButton.clicked.connect(self.manAddPortPair)

        self.manRemovebutton = QPushButton("Remove ports")
        self.manRemovebutton.clicked.connect(self.manRemovePortPairLeft)
        self.manRemovebutton.clicked.connect(self.manRemovePortPairRight)

        self.modifyPortButton = QPushButton("Modify")
        self.modifyPortButton.clicked.connect(self.modifyPort)

        warning = QLabel("                Remove and modify function for Direct Ports are not fully functional, use with caution!")


        addRemoveButtons = QHBoxLayout()
        addRemoveButtons.addWidget(self.manAddButton)
        addRemoveButtons.addWidget(self.manRemovebutton)
        addRemoveButtons.addWidget(self.modifyPortButton)

        manPortLay.addWidget(manPortLabel)
        manPortLay.addWidget(manPortLabel2)
        manPortLay.addWidget(portlabelUpper)
        manPortLay.addWidget(self.manPortLeI)
        manPortLay.addWidget(portlabelLower)
        manPortLay.addWidget(self.manPortLeO)
        manPortLay.addLayout(qhbl3)
        manPortLay.addLayout(addRemoveButtons)
        manPortLay.addWidget(warning)
        # manPortLay.addWidget(self.manAddButton)
        # manPortLay.addItem(spaceManPort)
        # manPortLay.addWidget(self.manRemovebutton)
        # manPortLay.addItem(spaceManPort2)

        increaseSizeButton = QPushButton("Increase size")
        decreaseSizeButton = QPushButton("Decrease size")
        self.okButton = QPushButton("OK")
        self.cancelButton = QPushButton("Cancel")

        increaseSizeButton.clicked.connect(self.incrSize)
        decreaseSizeButton.clicked.connect(self.decrSize)
        self.okButton.clicked.connect(self.acceptedEdit)
        self.cancelButton.clicked.connect(self.cancel)

        L = QVBoxLayout()
        L.addWidget(description)
        L.addWidget(tankNameLabel)
        L.addWidget(self.le)

        # L.addWidget(connectionsLabelL)
        # L.addWidget(self.leCNL)
        # L.addWidget(connectionsLabelR)
        # L.addWidget(self.leCNR)
        # L.addWidget(addSideAutoButton)
        # L.addItem(spaceVBox)

        t1Layout = QVBoxLayout()
        t1Layout.addLayout(qhbL)
        t1Layout.addLayout(gl)

        self.tab1.setLayout(t1Layout)

        self.tab2.setLayout(manPortLay)

        L.addWidget(self.tabs)

        L.addWidget(increaseSizeButton)
        L.addWidget(decreaseSizeButton)
        L.addWidget(self.okButton)
        L.addWidget(self.cancelButton)

        self.setLayout(L)

        self.loadHxL()
        self.loadDirPorts()

        # This is to ensure that only one list element is selected
        self.listWR.setSelectionMode(1)
        self.listWL.setSelectionMode(1)
        self.listWR.clicked.connect(self.listWRClicked)
        self.listWL.clicked.connect(self.listWLClicked)

        self.listWR2.setSelectionMode(1)
        self.listWL2.setSelectionMode(1)
        self.listWR2.clicked.connect(self.listWR2Clicked)
        self.listWL2.clicked.connect(self.listWL2Clicked)

        self.show()

    def loadHxL(self):
        for h in self.storage.heatExchangers:
            if h.sSide == 0:
                self.listWL.addItem(
                    h.displayName + ", y_offset = " + "%.2f" %(100 - 100 * h.offset.y() / self.storage.h) + "%")
            if h.sSide == 2:
                self.listWR.addItem(
                    h.displayName + ", y_offset = " + "%.2f" %(100 - 100 * h.offset.y() / self.storage.h) + "%")

    def loadDirPorts(self):
        for c in self.storage.directPortConnsForList:
            if c.fromPort.side == 0:
                listW = self.listWL2
            else:
                listW = self.listWR2
            listW.addItem(c.displayName + ',' + "Port pair from " + "%d%%" % (100 - 100 * c.fromPort.pos().y() / self.storage.h) +
                          " to " + "%d%%" % (100 - 100 * c.toPort.pos().y() / self.storage.h))

    # Unused
    def addPortPairToList(self, p):
        if not p.isFromHx:
            if p.side == 2:
                listW = self.listWR2
            else:
                listW = self.listWL2

            if p.connectionList[0].fromPort is p:
                otherPort = p.connectionList[0].toPort
            else:
                otherPort = p.connectionList[0].fromPort

            listW.addItem("Port pair from " + "%0.2f" % (100 - 100 * p.pos().y() / self.storage.h) +
                          " to " + "%0.2f" % (100 - 100 * otherPort.pos().y() / self.storage.h))

    def listWLClicked(self):
        self.listWR.clearSelection()

    def listWRClicked(self):
        self.listWL.clearSelection()

    def listWL2Clicked(self):
        self.listWR2.clearSelection()

    def listWR2Clicked(self):
        self.listWL2.clearSelection()


    def addHx(self):
        """
        Checks whether the inputs are in the correct range [0,100] and in order, and calls the function for creating a
        HeatExchanger on the respective side.

        Returns
        -------

        """
        if self.minOffsetDistance() and float(self.offsetLeI.text()) > float(self.offsetLeO.text() and self.offsetsInRange()):
            print("Adding hx")
            if self.rButton.isChecked():
                print("addhxr")
                self.addHxR()
            if self.lButton.isChecked():
                print("addhxl")
                self.addHxL()
        else:
            print("At least 20% of difference and larger top port than bottom port needed and valid range [0, 100]")

    def minOffsetDistance(self):
        return abs(float(self.offsetLeI.text()) - float(self.offsetLeO.text())) >= 20

    def offsetsInRange(self):
        return (0 < float(self.offsetLeI.text()) < 100) and (0 < float(self.offsetLeO.text()) < 100)

    def addHxL(self):
        """
        Creates a HeatExchanger on the left side and adds it to the listWL
        The comma in the display string of listWL is crucial, since the removeHx function takes the string until the
        comma as name of the Heatexchanger to delete.

        Returns
        -------

        """
        hx_temp = HeatExchanger(0, self.w_hx, abs(
            1 / 100 * self.storage.h * (float(self.offsetLeO.text()) - float(self.offsetLeI.text()))),
                                QPointF(0, self.storage.h - 1 / 100 * float(self.offsetLeI.text()) * self.storage.h),
                                self.storage,
                                self.hxNameLe.text())

        # Add HeatExchanger string to list
        self.listWL.addItem(hx_temp.displayName + ", y_offsets = " + "%d" %(float(self.offsetLeI.text())) + "%")

    def addHxR(self):
        """
       Creates a HeatExchanger on the right side and adds it to the listWR
       The comma in the display string of listWR is crucial, since the removeHx function takes the string until the
       comma as name of the Heatexchanger to delete.

       Returns
       -------

        """
        hx_temp = HeatExchanger(2, self.w_hx, abs(
            1 / 100 * self.storage.h * (float(self.offsetLeO.text()) - float(self.offsetLeI.text()))),
                                QPointF(self.storage.w,
                                        self.storage.h - 1 / 100 * float(self.offsetLeI.text()) * self.storage.h),
                                self.storage,
                                self.hxNameLe.text())
        # Add HeatExchanger string to list
        self.listWR.addItem(hx_temp.displayName + ", y_offset = " + "%d" %(float(self.offsetLeI.text())) + "%")

    def manAddPortPair(self):
        if float(self.manPortLeI.text()) > float(self.offsetLeO.text()):
            self.storage.setSideManualPair(self.manlButton.isChecked(),
                                           (1 - 1 / 100 * float(self.manPortLeI.text())) * self.storage.h,
                                           (1 - 1 / 100 * float(self.manPortLeO.text())) * self.storage.h)

        self.listWL2.clear()
        self.listWR2.clear()
        self.loadDirPorts()
        print("After creating left side has:")
        for i in self.storage.leftSide:
            print(i.pos().y())

    def manRemovePortPairLeft(self):
        # print("Before delete, left side has:")
        # print(self.storage.leftSide)
        for i in self.storage.directPortConnsForList:
            print(self.storage.directPortConnsForList)
            for j in self.listWL2.selectedItems():
                if i.displayName == j.text()[:j.text().find(",")]:
                    print('i :' + i.displayName)
                    print('j : ' + j.text()[:j.text().find(",")])
                    self.storage.directPortConnsForList.remove(i)
                    self.listWL2.takeItem(self.listWL2.row(self.listWL2.selectedItems()[0]))

                    while len(i.fromPort.connectionList) > 0:
                        i.fromPort.connectionList[0].deleteConn()

                    while len(i.toPort.connectionList) > 0:
                        i.toPort.connectionList[0].deleteConn()

                    self.storage.inputs.remove(i.fromPort)
                    self.storage.outputs.remove(i.toPort)
                    self.storage.leftSide.remove(i.fromPort)
                    self.storage.leftSide.remove(i.toPort)

                    self.storage.parent.scene().removeItem(i.fromPort)
                    self.storage.parent.scene().removeItem(i.toPort)

                    self.storage.parent.scene().removeItem(i.fromPort)
                    self.storage.parent.scene().removeItem(i.toPort)
                    self.storage.parent.scene().removeItem(i.fromPort)
                    self.storage.parent.scene().removeItem(i.toPort)



        # print("After delete, left side has:")
        # print(self.storage.leftSide)

    def manRemovePortPairRight(self):
        for i in self.storage.directPortConnsForList:
            for j in self.listWR2.selectedItems():
                if i.displayName == j.text()[:j.text().find(",")]:
                    # print('i :' + i.displayName)
                    # print('j : ' + j.text()[:j.text().find(",")])
                    self.storage.directPortConnsForList.remove(i)
                    self.listWR2.takeItem(self.listWR2.row(self.listWR2.selectedItems()[0]))

                    while len(i.fromPort.connectionList) > 0:
                        i.fromPort.connectionList[0].deleteConn()

                    while len(i.toPort.connectionList) > 0:
                        i.toPort.connectionList[0].deleteConn()

                    self.storage.inputs.remove(i.fromPort)
                    self.storage.outputs.remove(i.toPort)
                    self.storage.rightSide.remove(i.fromPort)
                    self.storage.rightSide.remove(i.toPort)

                    self.storage.parent.scene().removeItem(i.fromPort)
                    self.storage.parent.scene().removeItem(i.toPort)

                    self.storage.parent.scene().removeItem(i.fromPort)
                    self.storage.parent.scene().removeItem(i.toPort)
                    self.storage.parent.scene().removeItem(i.fromPort)
                    self.storage.parent.scene().removeItem(i.toPort)



    def removeHxL(self):
        for i in self.storage.heatExchangers:
            # Name is identified through index of comma
            for j in self.listWL.selectedItems():
                # print('printing display name: ' + i.displayName + '\n')
                # print('printing j.text: ' + j.text())
                if i.displayName == j.text()[:j.text().find(",")]:
                    self.storage.heatExchangers.remove(i)
                    self.listWL.takeItem(self.listWL.row(self.listWL.selectedItems()[0]))

                    # for c in i.port1.connectionList:
                    while len(i.port1.connectionList) > 0:
                        i.port1.connectionList[0].deleteConn()

                    # for c in i.port2.connectionList:
                    while len(i.port2.connectionList) > 0:
                        i.port2.connectionList[0].deleteConn()

                    self.storage.inputs.remove(i.port1)
                    self.storage.outputs.remove(i.port2)

                    self.storage.parent.scene().removeItem(i.port1)
                    self.storage.parent.scene().removeItem(i.port2)
                    self.storage.parent.scene().removeItem(i)

        # self.storage.h -= self.h_hx
        # self.storage.updateImage(-self.h_hx)

    def removeHxR(self):
        for i in self.storage.heatExchangers:
            # Name is identified through index of comma
            for j in self.listWR.selectedItems():
                if i.displayName == j.text()[:j.text().find(",")]:
                    self.storage.heatExchangers.remove(i)
                    self.listWR.takeItem(self.listWR.row(self.listWR.selectedItems()[0]))

                    # for c in i.port1.connectionList:
                    while len(i.port1.connectionList) > 0:
                        i.port1.connectionList[0].deleteConn()

                    # for c in i.port2.connectionList:
                    while len(i.port2.connectionList) > 0:
                        i.port2.connectionList[0].deleteConn()

                    self.storage.inputs.remove(i.port1)
                    self.storage.outputs.remove(i.port2)

                    self.storage.parent.scene().removeItem(i.port1)
                    self.storage.parent.scene().removeItem(i.port2)
                    self.storage.parent.scene().removeItem(i)

    def modifyHx(self):
        # print("Left: ")
        # print(self.listWL.selectedItems())
        # print("\nRight: ")
        # print(self.listWR.selectedItems())
        if len(self.listWL.selectedItems()) == 0 and len(self.listWR.selectedItems()) == 0:
            return
        else:
            if self.rButton.isChecked() or self.lButton.isChecked():
                self.addHx()
                self.removeHxL()
                self.removeHxR()

    def modifyPort(self):
        # xValue = 0
        # if self.listWL2.selectedItems() is not None:
        #     self.manRemovePortPairLeft()
        #     xValue += 1
        #     print("1st if is ran")
        #     print(self.listWL2.selectedItems())
        # if self.listWR2.selectedItems() is not None:
        #     self.manRemovePortPairRight()
        #     xValue += 1
        #     print("2nd if is ran")
        #     print(self.listWR2.selectedItems())
        # if xValue != 0:
        #     self.manAddPortPair()

        if len(self.listWL2.selectedItems()) == 0 and len(self.listWR2.selectedItems()) == 0:
            return
        elif len(self.listWL2.selectedItems()) > 0:
            self.manRemovePortPairLeft()
        elif len(self.listWR2.selectedItems()) > 0:
            self.manRemovePortPairRight()
        self.manAddPortPair()


    # self.storage.h -= self.h_hx
    # self.storage.updateImage(-self.h_hx)
    def incrSize(self):
        self.storage.updatePortPositionsHW(self.h_hx, self.w_hx)
        self.storage.updateHxLines(self.h_hx)
        self.storage.h += self.h_hx
        self.storage.w += self.w_hx
        self.storage.updateImage()

    # Unused
    def decrSize(self):
        self.storage.updatePortPositionsDecHW(self.h_hx, self.w_hx)
        self.storage.updateHxLines(-self.h_hx)
        self.storage.h -= self.h_hx
        self.storage.w -= self.w_hx
        self.storage.updateImage()

    def acceptedEdit(self):
        # print("Changing displayName")
        self.storage.setName(self.le.text())
        self.close()

    def cancel(self):
        self.close()
