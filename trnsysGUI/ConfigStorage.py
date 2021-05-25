# pylint: skip-file
# type: ignore

import enum as _enum

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QLabel,
    QLineEdit,
    QGridLayout,
    QHBoxLayout,
    QListWidget,
    QPushButton,
    QSpacerItem,
    QVBoxLayout,
    QRadioButton,
    QDialog,
    QTabWidget,
    QWidget,
    QMessageBox,
)

import trnsysGUI.DirectPortPair as _dpp
from trnsysGUI.HeatExchanger import HeatExchanger


class Side(_enum.Enum):
    LEFT = _enum.auto()
    RIGHT = _enum.auto()


class ConfigStorage(QDialog):
    HEAT_EXCHANGER_WIDTH = 40
    WIDTH_INCREMENT = 10
    HEIGHT_INCREMENT = 100

    def __init__(self, storage, parent):
        super(ConfigStorage, self).__init__(parent)
        self.parent = parent
        self.storage = storage
        self.n = 0
        self.m = 0

        spacerHeight = 15

        self.tabs = QTabWidget()
        self.tab1 = QWidget()
        self.tab2 = QWidget()

        self.tabs.addTab(self.tab1, "Heat exchangers")
        self.tabs.addTab(self.tab2, "Direct ports")

        h0 = QHBoxLayout()
        description = QLabel("Please configure the storage tank:")
        exportButton = QPushButton("Export ddck")
        exportButton.clicked.connect(self.storage.exportDck)

        h0.addWidget(description)
        h0.addWidget(exportButton)

        tankNameLabel = QLabel()
        tankNameLabel.setText("<b>Tank name: </b>")
        self.le = QLineEdit(self.storage.label.toPlainText())

        gl = QGridLayout()
        hxsLabel = QLabel("<b>Heat Exchangers </b>")
        gl.addWidget(hxsLabel, 0, 0, 1, 2)

        qhbL = QHBoxLayout()

        self.leftHeatExchangersItemListWidget = QListWidget()
        qhbL.addWidget(self.leftHeatExchangersItemListWidget)

        self.rightHeatExchangersItemListWidget = QListWidget()
        qhbL.addWidget(self.rightHeatExchangersItemListWidget)

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

        self._leftDirectPortPairsItemListWidget = QListWidget()
        qhbL2.addWidget(self._leftDirectPortPairsItemListWidget)

        self._rightDirectPortPairsItemListWidget = QListWidget()
        qhbL2.addWidget(self._rightDirectPortPairsItemListWidget)

        manPortLay.addLayout(qhbL2)

        manPortLabel = QLabel("<b>Set port manually</b>")
        manPortLabel2 = QLabel("Enter height in percent: ")
        portlabelUpper = QLabel("Inlet")
        self.manPortLeI = QLineEdit("0")
        portlabelLower = QLabel("Outlet")
        self.manPortLeO = QLineEdit("0")

        qhbl3 = QHBoxLayout()
        self.manlButton = QRadioButton("Left side")
        self.manrButton = QRadioButton("Right side")
        qhbl3.addWidget(self.manlButton)
        qhbl3.addWidget(self.manrButton)

        self.manAddButton = QPushButton("Add (manual) ports")
        self.manAddButton.clicked.connect(self.manAddPortPair)

        self.manRemovebutton = QPushButton("Remove ports")
        self.manRemovebutton.clicked.connect(self.manRemovePortPairLeft)
        self.manRemovebutton.clicked.connect(self.manRemovePortPairRight)

        self.modifyPortButton = QPushButton("Modify")
        self.modifyPortButton.clicked.connect(self.modifyPort)

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

        increaseSizeButton = QPushButton("Increase size")
        decreaseSizeButton = QPushButton("Decrease size")
        self.okButton = QPushButton("OK")
        self.cancelButton = QPushButton("Cancel")

        increaseSizeButton.clicked.connect(self.incrSize)
        decreaseSizeButton.clicked.connect(self.decrSize)
        self.okButton.clicked.connect(self.acceptedEdit)
        self.cancelButton.clicked.connect(self.cancel)

        L = QVBoxLayout()
        L.addLayout(h0)
        L.addWidget(tankNameLabel)
        L.addWidget(self.le)

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

        self._loadHeatExchangers()
        self._loadDirectPortPairs()

        # This is to ensure that only one list element is selected
        self.rightHeatExchangersItemListWidget.setSelectionMode(1)
        self.leftHeatExchangersItemListWidget.setSelectionMode(1)
        self.rightHeatExchangersItemListWidget.clicked.connect(self.listWRClicked)
        self.leftHeatExchangersItemListWidget.clicked.connect(self.listWLClicked)

        self._rightDirectPortPairsItemListWidget.setSelectionMode(1)
        self._leftDirectPortPairsItemListWidget.setSelectionMode(1)
        self._rightDirectPortPairsItemListWidget.clicked.connect(self.listWR2Clicked)
        self._leftDirectPortPairsItemListWidget.clicked.connect(self.listWL2Clicked)

        self.show()

    def _loadHeatExchangers(self):
        for h in self.storage.heatExchangers:
            listItem = self._createHeatExchangerListItem(h)
            if h.sSide == 0:
                self.leftHeatExchangersItemListWidget.addItem(listItem)
            if h.sSide == 2:
                self.rightHeatExchangersItemListWidget.addItem(listItem)

    @staticmethod
    def _createHeatExchangerListItem(h):
        return (
            h.displayName
            + ", y_offset = "
            + "%d" % int(h.relativeInputHeight * 100)
            + "%"
            + " to "
            + "%d" % int(h.relativeOutputHeight * 100)
            + "%"
        )

    def _loadDirectPortPairs(self):
        directPortPair: _dpp.DirectPortPair
        for directPortPair in self.storage.directPortPairs:
            listItem = self._createDirectPortPairListItem(directPortPair)

            if directPortPair.isOnLeftSide:
                self._leftDirectPortPairsItemListWidget.addItem(listItem)
            else:
                self._rightDirectPortPairsItemListWidget.addItem(listItem)

    @staticmethod
    def _createDirectPortPairListItem(directPortPair: _dpp.DirectPortPair):
        return (
            directPortPair.connection.displayName
            + ","
            + "Port pair from "
            + "%d%%" % int(directPortPair.relativeInputHeight * 100)
            + " to "
            + "%d%%" % int(directPortPair.relativeOutputHeight * 100)
        )

    def listWLClicked(self):
        self.rightHeatExchangersItemListWidget.clearSelection()

    def listWRClicked(self):
        self.leftHeatExchangersItemListWidget.clearSelection()

    def listWL2Clicked(self):
        self._rightDirectPortPairsItemListWidget.clearSelection()

    def listWR2Clicked(self):
        self._leftDirectPortPairsItemListWidget.clearSelection()

    def addHx(self):
        """
        Checks whether the inputs are in the correct range [0,100] and in order, and calls the function for creating a
        HeatExchanger on the respective side.

        Returns
        -------
        """
        if (
            self.minOffsetDistance()
            and float(self.offsetLeI.text()) > float(self.offsetLeO.text())
            and self.offsetsInRange()
        ):
            print("Adding hx")
            if self.rButton.isChecked():
                print("addhxr")
                self.addHxR()
            if self.lButton.isChecked():
                print("addhxl")
                self.addHxL()
        else:
            msgb = QMessageBox()
            msgb.setText(
                "At least 20% of difference and larger top port than bottom port needed and valid range [0, 100]"
            )
            msgb.exec_()

    def minOffsetDistance(self):
        return abs(float(self.offsetLeI.text()) - float(self.offsetLeO.text())) >= 5

    def offsetsInRange(self):
        return (0 <= float(self.offsetLeI.text()) <= 100) and (
            0 <= float(self.offsetLeO.text()) <= 100
        )

    def addHxL(self):
        self._addHeatExchanger(Side.LEFT)

    def addHxR(self):
        self._addHeatExchanger(Side.RIGHT)

    def _addHeatExchanger(self, side: Side):
        name = self.hxNameLe.text()
        if not name:
            messageBox = QMessageBox()
            messageBox.setText(
                "Please specify the name of the heat exchanger that you want to add."
            )
            messageBox.exec_()
            return

        relativeInputHeight = float(self.offsetLeI.text()) / 100
        relativeOutputHeight = float(self.offsetLeO.text()) / 100

        heatExchanger = HeatExchanger(
            sideNr=0 if side == Side.LEFT else 2,
            width=self.HEAT_EXCHANGER_WIDTH,
            relativeInputHeight=relativeInputHeight,
            relativeOutputHeight=relativeOutputHeight,
            storageTankWidth=self.storage.w,
            storageTankHeight=self.storage.h,
            parent=self.storage,
            name=name,
            tempHx=True,
        )

        listItem = self._createHeatExchangerListItem(heatExchanger)
        if side == Side.LEFT:
            self.leftHeatExchangersItemListWidget.addItem(listItem)
        else:
            self.rightHeatExchangersItemListWidget.addItem(listItem)

    def manAddPortPair(self):
        if float(self.manPortLeI.text()) > 100:
            self.manPortLeI.setText("100")

        if float(self.manPortLeO.text()) < 0:
            self.manPortLeO.setText("0")

        self.storage.createAndAddDirectPortPair(
            self.manlButton.isChecked(),
            float(self.manPortLeI.text()) / 100,
            float(self.manPortLeO.text()) / 100,
            self.storage.h,
        )

        self._leftDirectPortPairsItemListWidget.clear()
        self._rightDirectPortPairsItemListWidget.clear()
        self._loadDirectPortPairs()

    def manRemovePortPairLeft(self):
        self._removeSelectedPortPairs(self._leftDirectPortPairsItemListWidget)

    def manRemovePortPairRight(self):
        self._removeSelectedPortPairs(self._rightDirectPortPairsItemListWidget)

    def _removeSelectedPortPairs(self, directPortPairsListWidget):
        for listItem in directPortPairsListWidget.selectedItems():
            for directPortPair in list(self.storage.directPortPairs):
                connection = directPortPair.connection

                if (
                    connection.displayName
                    == listItem.text()[: listItem.text().find(",")]
                ):
                    self.storage.directPortPairs.remove(directPortPair)
                    directPortPairsListWidget.takeItem(
                        directPortPairsListWidget.row(
                            directPortPairsListWidget.selectedItems()[0]
                        )
                    )

                    while len(connection.fromPort.connectionList) > 0:
                        connection.fromPort.connectionList[0].deleteConn()

                    while len(connection.toPort.connectionList) > 0:
                        connection.toPort.connectionList[0].deleteConn()

                    self.storage.inputs.remove(connection.fromPort)
                    self.storage.outputs.remove(connection.toPort)

                    self.storage.parent.scene().removeItem(connection.fromPort)
                    self.storage.parent.scene().removeItem(connection.toPort)

    def removeHxL(self):
        self._removeSelectedHeatExchangers(self.leftHeatExchangersItemListWidget)

    def removeHxR(self):
        self._removeSelectedHeatExchangers(self.rightHeatExchangersItemListWidget)

    def _removeSelectedHeatExchangers(self, heatExchangersItemListWidget):
        for listItem in heatExchangersItemListWidget.selectedItems():
            for heatExchanger in list(self.storage.heatExchangers):
                if (
                    heatExchanger.displayName
                    == listItem.text()[: listItem.text().find(",")]
                ):
                    self.storage.heatExchangers.remove(heatExchanger)
                    heatExchangersItemListWidget.takeItem(
                        heatExchangersItemListWidget.row(
                            heatExchangersItemListWidget.selectedItems()[0]
                        )
                    )

                    while len(heatExchanger.port1.connectionList) > 0:
                        heatExchanger.port1.connectionList[0].deleteConn()

                    while len(heatExchanger.port2.connectionList) > 0:
                        heatExchanger.port2.connectionList[0].deleteConn()

                    self.storage.inputs.remove(heatExchanger.port1)
                    self.storage.outputs.remove(heatExchanger.port2)

                    self.storage.parent.scene().removeItem(heatExchanger.port1)
                    self.storage.parent.scene().removeItem(heatExchanger.port2)
                    self.storage.parent.scene().removeItem(heatExchanger)

    def modifyHx(self):
        """
        Modify Hx.
        """
        result = self._getFirstSelectedItemAndHeatExchanger()

        if not result:
            return

        selectedItem, heatExchanger = result

        inputHeight = f"{heatExchanger.relativeInputHeight * 100}%"
        outputHeight = f"{heatExchanger.relativeOutputHeight * 100}%"

        dialogResult = modifyDialog(inputHeight, outputHeight)

        if dialogResult.cancelled:
            return

        heatExchanger.modifyPosition(dialogResult.newPortHeights)

        listText = self._createHeatExchangerListItem(heatExchanger)

        selectedItem.setText(listText)

    def _getFirstSelectedItemAndHeatExchanger(self):
        leftSelectedItems = self.leftHeatExchangersItemListWidget.selectedItems()
        rightSelectedItems = self.rightHeatExchangersItemListWidget.selectedItems()

        if leftSelectedItems:
            side = 0
            selectedItem = leftSelectedItems[0]
        elif rightSelectedItems:
            side = 2
            selectedItem = rightSelectedItems[0]
        else:
            return None

        name = selectedItem.text().split(",")[0]
        for heatExchanger in self.storage.heatExchangers:
            if heatExchanger.displayName == name and heatExchanger.sSide == side:
                return selectedItem, heatExchanger

        raise AssertionError(f"No heat exchanger with name {name} found.")

    def modifyPort(self):
        """
        Modify existing ports.
        """
        side = ""
        noSelection = True
        try:
            connectionName, residualInfo = (
                self._leftDirectPortPairsItemListWidget.selectedItems()[0]
                .text()
                .split(",")
            )
            side = "Left"
            noSelection = False
        except:
            pass
        try:
            connectionName, residualInfo = (
                self._rightDirectPortPairsItemListWidget.selectedItems()[0]
                .text()
                .split(",")
            )
            side = "Right"
            noSelection = False
        except:
            pass

        if noSelection:
            return

        residualInfo = residualInfo.split(" ")
        inputHeight = residualInfo[3]
        outputHeight = residualInfo[5]

        dialogResult = modifyDialog(inputHeight, outputHeight)

        if dialogResult.cancelled:
            return

        self.storage.modifyPortPosition(connectionName, dialogResult.newPortHeights)

        textPorts = dialogResult.newPortHeights

        if str(textPorts[0]) == "":
            textPorts[0] = inputHeight
        else:
            textPorts[0] = str(round(textPorts[0])) + "%"
        if str(textPorts[1]) == "":
            textPorts[1] = outputHeight
        else:
            textPorts[1] = str(round(textPorts[1])) + "%"

        listText = (
            connectionName
            + ","
            + residualInfo[0]
            + " "
            + residualInfo[1]
            + " "
            + residualInfo[2]
            + " "
            + textPorts[0]
            + " "
            + residualInfo[4]
            + " "
            + textPorts[1]
        )

        if side == "Left":
            self._leftDirectPortPairsItemListWidget.selectedItems()[0].setText(listText)
        elif side == "Right":
            self._rightDirectPortPairsItemListWidget.selectedItems()[0].setText(
                listText
            )

    def incrSize(self):
        self._changeSize(self.HEIGHT_INCREMENT, self.WIDTH_INCREMENT)

    def decrSize(self):
        self._changeSize(-self.HEIGHT_INCREMENT, -self.WIDTH_INCREMENT)

    def _changeSize(self, deltaH, deltaW):
        self.storage.updatePortItemPositions(deltaH, deltaW)
        self.storage.h += deltaH
        self.storage.w += deltaW
        self.storage.updateHeatExchangersAfterTankSizeChange()
        self.storage.updateImage()

    def acceptedEdit(self):
        # print("Changing displayName")
        test = self.le.text()
        if self.le.text() == "":
            qmb = QMessageBox()
            qmb.setText("Please set a name for this storage tank.")
            qmb.setStandardButtons(QMessageBox.Ok)
            qmb.setDefaultButton(QMessageBox.Ok)
            qmb.exec()
            return
        self.storage.setName(self.le.text())
        self.close()

    def cancel(self):
        self.close()


class modifyDialog(QDialog):
    """
    A dialog box lets the user choose the path and the name of folder for a new project
    """

    def __init__(self, inputHeight, outputHeight, parent=None):

        super(modifyDialog, self).__init__(parent)

        self.executed = False
        self.cancelled = True

        self.enteredPortHeights = ["", ""]
        self.newPortHeights = []

        newInputHeight = QLabel("Input currently at\t" + inputHeight + "\tnew (%):")
        self.line1 = QLineEdit()

        newOutputHeight = QLabel("Output currently at\t" + outputHeight + "\tnew (%):")
        self.line2 = QLineEdit()

        inputHeightLayout = QHBoxLayout()
        inputHeightLayout.addWidget(newInputHeight)
        inputHeightLayout.addWidget(self.line1)

        newOutputLayout = QHBoxLayout()
        newOutputLayout.addWidget(newOutputHeight)
        newOutputLayout.addWidget(self.line2)

        self.okButton = QPushButton("Done")
        self.okButton.setFixedWidth(50)
        buttonLayout = QHBoxLayout()
        buttonLayout.addWidget(self.okButton, alignment=Qt.AlignCenter)

        overallLayout = QVBoxLayout()
        overallLayout.addLayout(inputHeightLayout)
        overallLayout.addLayout(newOutputLayout)
        overallLayout.addLayout(buttonLayout)
        self.setLayout(overallLayout)
        self.setFixedWidth(400)

        self.okButton.clicked.connect(self.doneEdit)
        self.setWindowTitle("Modify direct port couple")
        self.exec()

    def doneEdit(self):

        self.projectPathFlag = False
        self.folderNameFlag = False
        self.overwriteFolder = True

        self.enteredPortHeights = [self.line1.text(), self.line2.text()]
        portNames = ["Input", "Output"]

        for i in range(0, 2):
            if self.enteredPortHeights[i] != "":
                try:
                    portHeight = int(self.enteredPortHeights[i])
                    if portHeight < 1 or portHeight > 100:
                        msgBox = QMessageBox()
                        msgBox.setText(
                            portNames[i] + " needs to be between 1 and 100 %."
                        )
                        msgBox.exec()
                        return
                    else:
                        self.enteredPortHeights[i] = portHeight
                except:
                    msgBox = QMessageBox()
                    msgBox.setText(
                        "Invalid value for " + portNames[i].lower() + " port height."
                    )
                    msgBox.exec()
                    return

        self.newPortHeights = self.enteredPortHeights
        self.executed = True
        self.close()

    def closeEvent(self, e):
        if self.executed:
            self.cancelled = False
        e.accept()
