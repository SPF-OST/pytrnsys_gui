from PyQt5.QtCore import QPointF
from PyQt5.QtWidgets import QLabel, QLineEdit, QGridLayout, QHBoxLayout, QListWidget, QPushButton, QSpacerItem, \
    QVBoxLayout, QRadioButton, QDialog

from trnsysGUI.HeatExchanger import HeatExchanger


class ConfigStorage(QDialog):
    def __init__(self, storage, parent):
        super(ConfigStorage, self).__init__(parent)
        self.parent = parent
        self.storage = storage
        self.n = 0
        self.m = 0

        # Parameters:
        self.w_hx = 40
        self.h_hx = 60
        spacerHeight = 15

        # VBoxLayout
        description = QLabel("Please configure the storage tank:")
        tankNameLabel = QLabel()
        tankNameLabel.setText("<b>Tank name: </b>")
        self.le = QLineEdit(self.storage.label.toPlainText())

        connectionsLabelL = QLabel()
        connectionsLabelL.setText("<b>Left (distributed) Ports: </b>")
        self.leCNL = QLineEdit(str(len(self.storage.inputs)))

        connectionsLabelR = QLabel()
        connectionsLabelR.setText("<b>Right (distributed) Ports: </b>")
        self.leCNR = QLineEdit(str(len(self.storage.outputs)))

        addSideAutoButton = QPushButton("Add (distributed) ports")
        addSideAutoButton.clicked.connect(self.addSideAuto)
        spaceVBox = QSpacerItem(self.width(), spacerHeight)

        # Grid layout
        gl = QGridLayout()
        hxsLabel = QLabel("<b>Heat Exchangers </b>")
        # spinBox = QSpinBox()
        gl.addWidget(hxsLabel, 0, 0, 1, 2)
        # gl.addWidget(spinBox, 1, 0, 1, 2)

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
        gl.addWidget(self.offsetLeI, 5, 0, 1, 2)
        gl.addWidget(offsetLeOLabel, 6, 0, 1, 1)
        gl.addWidget(self.offsetLeO, 7, 0, 1, 2)

        # hxsideHbL = QHBoxLayout()
        # hxsideHbL.addWidget(self.lButton)
        # hxsideHbL.addWidget(self.rButton)

        # gl.addLayout(hxsideHbL, 6, 0)
        self.hxNameLe = QLineEdit()
        self.hxNameLe.setPlaceholderText("Enter a name...")
        gl.addWidget(self.hxNameLe, 8, 0, 1, 2)

        gl.addWidget(self.lButton, 9, 0, 1, 1)
        gl.addWidget(self.rButton, 9, 1, 1, 1)

        addButton = QPushButton("Add...")
        addButton.clicked.connect(self.addHx)
        gl.addWidget(addButton, 10, 0, 1, 1)
        removeButton = QPushButton("Remove...")
        removeButton.clicked.connect(self.removeHxL)
        removeButton.clicked.connect(self.removeHxR)
        gl.addWidget(removeButton, 10, 1, 1, 1)
        spaceHx = QSpacerItem(self.width(), spacerHeight)
        gl.addItem(spaceHx, 11, 0, 1, 2)

        manPortLay = QVBoxLayout()
        manPortLabel = QLabel("<b>Set port manually</b>")
        manPortLabel2 = QLabel("Enter height in percent: ")
        portlabelUpper = QLabel("Upper port")
        self.manPortLeI = QLineEdit("0")
        portlabelLower = QLabel("Lower port")
        self.manPortLeO = QLineEdit("0")
        self.manrButton = QRadioButton("Right side")
        self.manlButton = QRadioButton("Left side")
        self.manAddButton = QPushButton("Add (manual) ports")
        spaceManPort = QSpacerItem(self.width(), spacerHeight)
        self.manAddButton.clicked.connect(self.manAddPortPair)

        manPortLay.addWidget(manPortLabel)
        manPortLay.addWidget(manPortLabel2)
        manPortLay.addWidget(portlabelUpper)
        manPortLay.addWidget(self.manPortLeI)
        manPortLay.addWidget(portlabelLower)
        manPortLay.addWidget(self.manPortLeO)
        manPortLay.addWidget(self.manlButton)
        manPortLay.addWidget(self.manrButton)
        manPortLay.addWidget(self.manAddButton)
        manPortLay.addItem(spaceManPort)

        increaseSizeButton = QPushButton("Increase size")
        self.okButton = QPushButton("OK (change name)")
        self.cancelButton = QPushButton("Cancel")

        increaseSizeButton.clicked.connect(self.incrSize)
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

        L.addLayout(qhbL)
        L.addLayout(gl)
        L.addLayout(manPortLay)

        L.addWidget(increaseSizeButton)
        L.addWidget(self.okButton)
        L.addWidget(self.cancelButton)

        self.setLayout(L)

        self.loadHxL()

        self.show()

    def addSideAuto(self):
        self.storage.setLeftSideAuto(int(self.leCNL.text()))
        self.storage.setRightSideAuto(int(self.leCNR.text()))

    def loadHxL(self):
        for h in self.storage.heatExchangers:
            if h.sSide == 0:
                self.listWL.addItem(
                    h.displayName + ", y_offset = " + "%.2f" %(100 - 100 * h.offset.y() / self.storage.h) + "%")
            if h.sSide == 2:
                self.listWR.addItem(
                    h.displayName + ", y_offset = " + "%.2f" %(100 - 100 * h.offset.y() / self.storage.h) + "%")

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
                print("addhxr")
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
        self.listWL.addItem(hx_temp.displayName + ", y_offsets = " + "%.2f" %(float(self.offsetLeI.text())) + "%")

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
        self.listWR.addItem(hx_temp.displayName + ", y_offset = " + "%.2f" %(float(self.offsetLeI.text())) + "%")

    def manAddPortPair(self):
        if float(self.manPortLeI.text()) > float(self.offsetLeO.text()):
            self.storage.setSideManualPair(self.manlButton.isChecked(),
                                           (1 - 1 / 100 * float(self.manPortLeI.text())) * self.storage.h,
                                           (1 - 1 / 100 * float(self.manPortLeO.text())) * self.storage.h)

    def removeHxL(self):
        for i in self.storage.heatExchangers:
            # Name is identified through index of comma
            for j in self.listWL.selectedItems():
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

    # self.storage.h -= self.h_hx
    # self.storage.updateImage(-self.h_hx)

    def incrSize(self):
        self.storage.updatePortPositions(self.h_hx)
        self.storage.updateHxLines(self.h_hx)
        self.storage.h += self.h_hx
        self.storage.updateImage()

    # Unused
    def decrSize(self):
        self.storage.updatePortPositions(self.h_hx)
        self.storage.h -= self.h_hx
        self.storage.updateImage()

    def acceptedEdit(self):
        # print("Changing displayName")
        self.storage.setName(self.le.text())
        self.close()

    def cancel(self):
        self.close()
